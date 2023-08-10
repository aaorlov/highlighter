from rapidfuzz.distance import Indel
from itertools import groupby, combinations
import spacy.parts_of_speech as POS
from re import sub
from edit import Edit

def is_punct(token):
    return token.pos == POS.PUNCT or token.text in punctuation

def char_cost(a, b):
    return 1-Indel.normalized_distance(a.text, b.text)

def merge_edits(seq):
    if seq: return [("X", seq[0][1], seq[-1][2], seq[0][3], seq[-1][4])]
    else: return seq

open_pos = {POS.ADJ, POS.AUX, POS.ADV, POS.NOUN, POS.VERB}

class Alignment:
    _open_pos = {POS.ADJ, POS.ADV, POS.NOUN, POS.VERB}

    def __init__(self, orig, cor):
        self.orig = orig
        self.cor = cor

        o_len = len(orig)
        c_len = len(cor)
        o_low = [o.lower for o in orig]
        c_low = [c.lower for c in cor]
        cost_matrix = [[0.0 for j in range(c_len+1)] for i in range(o_len+1)]
        op_matrix = [["O" for j in range(c_len+1)] for i in range(o_len+1)]
        for i in range(1, o_len+1):
            cost_matrix[i][0] = cost_matrix[i-1][0] + 1
            op_matrix[i][0] = "D"
        for j in range(1, c_len+1):
            cost_matrix[0][j] = cost_matrix[0][j-1] + 1
            op_matrix[0][j] = "I"
        for i in range(o_len):
            for j in range(c_len):
                if orig[i].orth == cor[j].orth:
                    cost_matrix[i+1][j+1] = cost_matrix[i][j]
                    op_matrix[i+1][j+1] = "M"
                else:
                    del_cost = cost_matrix[i][j+1] + 1
                    ins_cost = cost_matrix[i+1][j] + 1
                    trans_cost = float("inf")

                    sub_cost = cost_matrix[i][j] + self.get_sub_cost(orig[i], cor[j])
                    k = 1
                    while i-k >= 0 and j-k >= 0 and cost_matrix[i-k+1][j-k+1] != cost_matrix[i-k][j-k]:
                        if sorted(o_low[i-k:i+1]) == sorted(c_low[j-k:j+1]):
                            trans_cost = cost_matrix[i-k][j-k] + k
                            break
                        k += 1

                    costs = [trans_cost, sub_cost, ins_cost, del_cost]
                    l = costs.index(min(costs))
                    cost_matrix[i+1][j+1] = costs[l]
                    if   l == 0: op_matrix[i+1][j+1] = "T"+str(k+1)
                    elif l == 1: op_matrix[i+1][j+1] = "S"
                    elif l == 2: op_matrix[i+1][j+1] = "I"
                    else: op_matrix[i+1][j+1] = "D"

        self.cost_matrix = cost_matrix
        self.op_matrix = op_matrix

        i = len(op_matrix)-1
        j = len(op_matrix[0])-1
        align_seq = []
        while i + j != 0:
            op = op_matrix[i][j]
            if op in {"M", "S"}:
                align_seq.append((op, i-1, i, j-1, j))
                i -= 1
                j -= 1
            elif op == "D":
                align_seq.append((op, i-1, i, j, j))
                i -= 1
            elif op == "I":
                align_seq.append((op, i, i, j-1, j))
                j -= 1
            else:
                k = int(op[1:])
                align_seq.append((op, i-k, i, j-k, j))
                i -= k
                j -= k
        align_seq.reverse()
        self.align_seq = align_seq

    def get_rule_edits(self):
        edits = []
        for op, group in groupby(self.align_seq, lambda x: x[0][0] if x[0][0] in {"M", "T"} else False):
            group = list(group)
            if op == "M": continue
            elif op == "T":
                for seq in group:
                    edits.append(Edit(self.orig, self.cor, seq[1:]))
            else:
                processed = self.process_seq(group)
                for seq in processed:
                    edits.append(Edit(self.orig, self.cor, seq[1:]))
        return edits

    def process_seq(self, seq):
        if len(seq) <= 1: return seq
        ops = [op[0] for op in seq]
        if set(ops) == {"D"} or set(ops) == {"I"}: return merge_edits(seq)
        content = False
        combos = list(combinations(range(0, len(seq)), 2))
        combos.sort(key = lambda x: x[1]-x[0], reverse=True)
        for start, end in combos:
            if "S" not in ops[start:end+1]: continue
            o = self.orig[seq[start][1]:seq[end][2]]
            c = self.cor[seq[start][3]:seq[end][4]]
            if start == 0 and (o[0].tag_ == "POS" or c[0].tag_ == "POS"):
                return [seq[0]] + self.process_seq(seq[1:])
            if o[-1].tag_ == "POS" or c[-1].tag_ == "POS":
                return self.process_seq(seq[:end-1]) + merge_edits(seq[end-1:end+1]) + self.process_seq(seq[end+1:])
            if o[-1].lower == c[-1].lower:
                if start == 0 and ((len(o) == 1 and c[0].text[0].isupper()) or (len(c) == 1 and o[0].text[0].isupper())):
                    return merge_edits(seq[start:end+1]) + self.process_seq(seq[end+1:])
                if (len(o) > 1 and is_punct(o[-2])) or (len(c) > 1 and is_punct(c[-2])):
                    return self.process_seq(seq[:end-1]) + merge_edits(seq[end-1:end+1]) + self.process_seq(seq[end+1:])
            s_str = sub("['-]", "", "".join([tok.lower_ for tok in o]))
            t_str = sub("['-]", "", "".join([tok.lower_ for tok in c]))
            if s_str == t_str:
                return self.process_seq(seq[:start]) + merge_edits(seq[start:end+1]) + self.process_seq(seq[end+1:])
            pos_set = set([tok.pos for tok in o]+[tok.pos for tok in c])
            if len(o) != len(c) and (len(pos_set) == 1 or pos_set.issubset({POS.AUX, POS.PART, POS.VERB})):
                return self.process_seq(seq[:start]) + merge_edits(seq[start:end+1]) + self.process_seq(seq[end+1:])
            if end-start < 2:
                if len(o) == len(c) == 2:
                    return self.process_seq(seq[:start+1]) + self.process_seq(seq[start+1:])
                if (ops[start] == "S" and char_cost(o[0], c[0]) > 0.75) or (ops[end] == "S" and char_cost(o[-1], c[-1]) > 0.75):
                    return self.process_seq(seq[:start+1]) + self.process_seq(seq[start+1:])
                if end == len(seq)-1 and ((ops[-1] in {"D", "S"} and o[-1].pos == POS.DET) or (ops[-1] in {"I", "S"} and c[-1].pos == POS.DET)):
                    return self.process_seq(seq[:-1]) + [seq[-1]]
            if not pos_set.isdisjoint(open_pos): content = True
        if content: return merge_edits(seq)
        else: return seq

    def get_sub_cost(self, o, c):
        if o.lower == c.lower: return 0
        if o.lemma == c.lemma: lemma_cost = 0
        else: lemma_cost = 0.499
        if o.pos == c.pos: pos_cost = 0
        elif o.pos in self._open_pos and c.pos in self._open_pos: pos_cost = 0.25
        else: pos_cost = 0.5
        char_cost = Indel.normalized_distance(o.text, c.text)
        return lemma_cost + pos_cost + char_cost

    def __str__(self):
        orig = " ".join(["Orig:"]+[tok.text for tok in self.orig])
        cor = " ".join(["Cor:"]+[tok.text for tok in self.cor])
        cost_matrix = "\n".join(["Cost Matrix:"]+[str(row) for row in self.cost_matrix])
        op_matrix = "\n".join(["Operation Matrix:"]+[str(row) for row in self.op_matrix])
        seq = "Best alignment: "+str([a[0] for a in self.align_seq])
        return "\n".join([orig, cor, cost_matrix, op_matrix, seq])