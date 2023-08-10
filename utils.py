import spacy.symbols as POS
from lancaster import LancasterStemmer
from rapidfuzz.distance import Levenshtein

rare_pos = {"INTJ", "NUM", "SYM", "X"}
open_pos2 = {"ADJ", "ADV", "NOUN", "VERB"}
dep_map = {"acomp": "ADJ", "amod": "ADJ", "advmod": "ADV", "det": "DET", "prep": "PREP", "prt": "PART", "punct": "PUNCT"}
conts = {"'d", "'ll", "'m", "n't", "'re", "'s", "'ve"}
aux_conts = {"ca": "can", "sha": "shall", "wo": "will"}
pos_map = {
  "ADP": "ADP",
  "ADV": "ADV",
  "AUX": "VERB",
  "ADJ": "ADJ",
  '""':"PUNCT",
  "SP":"SPACE",
  "SPACE":"SPACE",
  "_SP":"SPACE",
  "EOL":"SPACE",
  "BES":"VERB",
  "HVS":"VERB",
  "ADD":"X",
  "GW":"X",
  "NFP":"X",
  "XX":"X",
  "#":"SYM",
  "$":"SYM",
  "''":"PUNCT",
  ",":"PUNCT",
  "-LRB-":"PUNCT",
  "-RRB-":"PUNCT",
  ".":"PUNCT",
  ":":"PUNCT",
  "PUNCT":"PUNCT",
  "AFX":"ADJ",
  "CCONJ":"CCONJ",
  "CONJ":"CCONJ",
  "SCONJ":"CCONJ",
  "CC":"CCONJ",
  "IN":"CCONJ",
  "CD":"NUM",
  "NUM":"NUM",
  "DET":"DET",
  "DT":"DET",
  "EX":"PRON",
  "FW":"X",
  "HYPH":"PUNCT",
  "PREP":"ADP",
  "JJ":"ADJ",
  "JJR":"ADJ",
  "JJS":"ADJ",
  "LS":"X",
  "MD":"VERB",
  "NIL":"X",
  "NN":"NOUN",
  "NNP":"NOUN",
  "NNPS":"NOUN",
  "PROPN":"PROPN",
  "NOUN":"PROPN",
  "NNS":"NOUN",
  "PDT":"DET",
  "PART":"PART",
  "POS":"PART",
  "PRON":"PRON",
  "PRP":"PRON",
  "PRP$":"DET",
  "RB":"ADV",
  "RBR":"ADV",
  "RBS":"ADV",
  "RP":"PART",
  "SYM":"SYM",
  "TO":"PART",
  "UH":"INTJ",
  "INTJ": "INTJ",
  "VB":"VERB",
  "VERB":"VERB",
  "VBD":"VERB",
  "VBG":"VERB",
  "VBN":"VERB",
  "VBP":"VERB",
  "VBZ":"VERB",
  "WDT":"DET",
  "WP":"PRON",
  "WP$":"DET",
  "WRB":"ADV",
  "X":"X",
  "``":"PUNCT"
}

stemmer = LancasterStemmer()

def classify(edit):
    if not edit.o_toks and not edit.c_toks:
        edit.type = "UNK"
    elif not edit.o_toks and edit.c_toks:
        op = "M:"
        cat = get_one_sided_type(edit.c_toks)
        edit.type = op+cat
    elif edit.o_toks and not edit.c_toks:
        op = "U:"
        cat = get_one_sided_type(edit.o_toks)
        edit.type = op+cat
    else:
        if edit.o_str == edit.c_str:
            edit.type = "UNK"
        elif edit.o_toks[-1].lower == edit.c_toks[-1].lower and (len(edit.o_toks) > 1 or len(edit.c_toks) > 1):
            all_o_toks = edit.o_toks[:]
            all_c_toks = edit.c_toks[:]
            edit.o_toks = edit.o_toks[:-1]
            edit.c_toks = edit.c_toks[:-1]
            edit = classify(edit)
            edit.o_toks = all_o_toks
            edit.c_toks = all_c_toks
        else:
            op = "R:"
            cat = get_two_sided_type(edit.o_toks, edit.c_toks)
            edit.type = op+cat
    return edit

def get_one_sided_type(toks):
    if len(toks) == 1:
        if toks[0].tag_ == "POS":
            return "NOUN:POSS"
        if toks[0].lower_ in conts:
            return "CONTR"
        if toks[0].lower_ == "to" and toks[0].pos == POS.PART and toks[0].dep_ != "prep":
            return "VERB:FORM"
    pos_list, dep_list = get_edit_info(toks)
    if set(dep_list).issubset({"aux", "auxpass"}):
        return "VERB:TENSE"
    if len(set(pos_list)) == 1 and pos_list[0] not in rare_pos:
        return pos_list[0]
    if len(set(dep_list)) == 1 and dep_list[0] in dep_map.keys():
        return dep_map[dep_list[0]]
    if set(pos_list) == {"PART", "VERB"}:
        return "VERB"
    else:
        return "OTHER"

def get_edit_info(toks):
    pos = []
    dep = []
    for tok in toks:
        pos.append(pos_map[tok.tag_])
        dep.append(tok.dep_)
    return pos, dep

def only_orth_change(o_toks, c_toks):
    o_join = "".join([o.lower_ for o in o_toks])
    c_join = "".join([c.lower_ for c in c_toks])
    if o_join == c_join:
        return True
    return False

def exact_reordering(o_toks, c_toks):
    o_set = sorted([o.lower_ for o in o_toks])
    c_set = sorted([c.lower_ for c in c_toks])
    if o_set == c_set:
        return True
    return False

def preceded_by_aux(o_tok, c_tok):
    if o_tok[0].dep_.startswith("aux") and c_tok[0].dep_.startswith("aux"):
        o_head = o_tok[0].head
        c_head = c_tok[0].head
        o_children = o_head.children
        c_children = c_head.children
        for o_child in o_children:
            if o_child.dep_.startswith("aux"):
                if o_child.text != o_tok[0].text:
                    for c_child in c_children:
                        if c_child.dep_.startswith("aux"):
                            if c_child.text != c_tok[0].text:
                                return True
                            break
                break
    else:
        o_deps = [o_dep.dep_ for o_dep in o_tok[0].children]
        c_deps = [c_dep.dep_ for c_dep in c_tok[0].children]
        if "aux" in o_deps or "auxpass" in o_deps:
            if "aux" in c_deps or "auxpass" in c_deps:
                return True
    return False

def get_two_sided_type(o_toks, c_toks):
    o_pos, o_dep = get_edit_info(o_toks)
    c_pos, c_dep = get_edit_info(c_toks)
    if only_orth_change(o_toks, c_toks):
        return "ORTH"
    if exact_reordering(o_toks, c_toks):
        return "WO"
    if len(o_toks) == len(c_toks) == 1:
        if o_toks[0].tag_ == "POS" or c_toks[0].tag_ == "POS":
            return "NOUN:POSS"
        if (o_toks[0].lower_ in conts or c_toks[0].lower_ in conts) and o_pos == c_pos:
            return "CONTR"
        if (o_toks[0].lower_ in aux_conts and c_toks[0].lower_ == aux_conts[o_toks[0].lower_]) or (c_toks[0].lower_ in aux_conts and o_toks[0].lower_ == aux_conts[c_toks[0].lower_]):
            return "CONTR"
        if o_toks[0].lower_ in aux_conts or c_toks[0].lower_ in aux_conts:
            return "VERB:TENSE"
        if {o_toks[0].lower_, c_toks[0].lower_} == {"was", "were"}:
            return "VERB:SVA"
        if o_toks[0].lemma == c_toks[0].lemma and o_pos[0] in open_pos2 and c_pos[0] in open_pos2:
            if o_pos == c_pos:
                if o_pos[0] == "ADJ":
                    return "ADJ:FORM"
                if o_pos[0] == "NOUN":
                    return "NOUN:NUM"
                if o_pos[0] == "VERB":
                    if preceded_by_aux(o_toks, c_toks):
                        return "VERB:FORM"
                    if o_toks[0].tag_ in {"VBG", "VBN"} or c_toks[0].tag_ in {"VBG", "VBN"}:
                        return "VERB:FORM"
                    if o_toks[0].tag_ == "VBD" or c_toks[0].tag_ == "VBD":
                        return "VERB:TENSE"
                    if o_toks[0].tag_ == "VBZ" or c_toks[0].tag_ == "VBZ":
                        return "VERB:SVA"
                    if o_dep[0].startswith("aux") and c_dep[0].startswith("aux"):
                        return "VERB:TENSE"
            if set(o_dep+c_dep).issubset({"acomp", "amod"}):
                return "ADJ:FORM"
            if o_pos[0] == "ADJ" and c_toks[0].tag_ == "NNS":
                return "NOUN:NUM"
            if c_toks[0].tag_ in {"VBG", "VBN"}:
                return "VERB:FORM"
            if c_toks[0].tag_ == "VBD":
                return "VERB:TENSE"
            if c_toks[0].tag_ == "VBZ":
                return "VERB:SVA"
            else:
                return "MORPH"
        if stemmer.stem(o_toks[0].text) == stemmer.stem(c_toks[0].text) and o_pos[0] in open_pos2 and c_pos[0] in open_pos2:
            return "MORPH"
        if o_dep[0].startswith("aux") and c_dep[0].startswith("aux"):
            return "VERB:TENSE"
        if o_pos == c_pos and o_pos[0] not in rare_pos:
            return o_pos[0]
        if o_dep == c_dep and o_dep[0] in dep_map.keys():
            return dep_map[o_dep[0]]
        if set(o_pos+c_pos) == {"PART", "PREP"} or \
                set(o_dep+c_dep) == {"prt", "prep"}:
            return "PART"
        if set(o_pos+c_pos) == {"DET", "PRON"}:
            if c_dep[0] in {"nsubj", "nsubjpass", "dobj", "pobj"}:
                return "PRON"
            if c_dep[0] == "poss":
                return "DET"
        if set(o_pos+c_pos) == {"NUM", "DET"}:
            return "DET"
        if {o_toks[0].lower_, c_toks[0].lower_} == {"other", "another"}:
            return "DET"
        if o_toks[0].lower_ == "your" and c_toks[0].lower_ == "yours":
            return "PRON"
        if {o_toks[0].lower_, c_toks[0].lower_} == {"no", "not"}:
            return "OTHER"
        if o_toks[0].text.isalpha() and c_toks[0].text.isalpha():
            str_sim = Levenshtein.normalized_similarity(o_toks[0].lower_, c_toks[0].lower_)
            if len(o_toks[0].text) == 1:
                if len(c_toks[0].text) == 2 and str_sim == 0.5:
                    return "SPELL"
            if len(o_toks[0].text) == 2:
                if 2 <= len(c_toks[0].text) <= 3 and str_sim >= 0.5:
                    return "SPELL"
            if len(o_toks[0].text) == 3:
                if o_toks[0].lower_ == "the" and c_toks[0].lower_ == "that":
                    return "PRON"
                if o_toks[0].lower_ == "all" and c_toks[0].lower_ == "everything":
                    return "PRON"
                if 2 <= len(c_toks[0].text) <= 4 and str_sim >= 0.5:
                    return "SPELL"
            if len(o_toks[0].text) == 4:
                if {o_toks[0].lower_, c_toks[0].lower_} == {"that", "what"}:
                    return "PRON"
                if {o_toks[0].lower_, c_toks[0].lower_} == {"good", "well"} and c_pos[0] not in rare_pos:
                    return c_pos[0]
                if len(c_toks[0].text) == 3 and str_sim > 0.5:
                    return "SPELL"
                if len(c_toks[0].text) == 4 and str_sim >= 0.5:
                    return "SPELL"
                if len(c_toks[0].text) == 5 and str_sim == 0.8:
                    return "SPELL"
                if len(c_toks[0].text) > 5 and str_sim > 0.5 and c_pos[0] not in rare_pos:
                    return c_pos[0]
            if len(o_toks[0].text) == 5:
                if {o_toks[0].lower_, c_toks[0].lower_} == {"after", "later"} and c_pos[0] not in rare_pos:
                    return c_pos[0]
                if len(c_toks[0].text) == 4 and str_sim == 0.8:
                    return "SPELL"
                if len(c_toks[0].text) == 5 and str_sim >= 0.6:
                    return "SPELL"
                if len(c_toks[0].text) > 5 and c_pos[0] not in rare_pos:
                    return c_pos[0]
            if len(o_toks[0].text) > 5 and len(c_toks[0].text) > 5:
                if o_toks[0].lower_ == "therefor" and c_toks[0].lower_ == "therefore":
                    return "SPELL"
                if {o_toks[0].lower_, c_toks[0].lower_} == {"though", "thought"}:
                    return "SPELL"
                if (o_toks[0].text.startswith(c_toks[0].text) or c_toks[0].text.startswith(o_toks[0].text)) and str_sim >= 0.66:
                    return "MORPH"
                if str_sim > 0.8:
                    return "SPELL"
                if str_sim < 0.55 and c_pos[0] not in rare_pos:
                    return c_pos[0]
        else:
            return "OTHER"
    if set(o_dep+c_dep).issubset({"aux", "auxpass"}):
        return "VERB:TENSE"
    if len(set(o_pos+c_pos)) == 1:
        if o_pos[0] == "VERB" and o_toks[-1].lemma == c_toks[-1].lemma:
            return "VERB:TENSE"
        elif o_pos[0] not in rare_pos:
            return o_pos[0]
    if len(set(o_dep+c_dep)) == 1 and o_dep[0] in dep_map.keys():
        return dep_map[o_dep[0]]
    if set(o_pos+c_pos) == {"PART", "VERB"}:
        if o_toks[-1].lemma == c_toks[-1].lemma:
            return "VERB:FORM"
        else:
            return "VERB"
    if (o_pos == ["NOUN", "PART"] or c_pos == ["NOUN", "PART"]) and o_toks[0].lemma == c_toks[0].lemma:
        return "NOUN:POSS"
    if (o_toks[0].lower_ in {"most", "more"} or c_toks[0].lower_ in {"most", "more"}) and o_toks[-1].lemma == c_toks[-1].lemma and len(o_toks) <= 2 and len(c_toks) <= 2:
        return "ADJ:FORM"
    else:
        return "OTHER"