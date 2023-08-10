import spacy
from spacy.tokens import Doc
from itertools import combinations, groupby
from rapidfuzz.distance import Indel
from alignment import Alignment
from utils import classify

nlp = spacy.load('en_core_web_sm')

def handler():
  orig_text = 'what'
  cor_text = '?what'
  orig = nlp(orig_text)
  cor = nlp(cor_text)
  alignment = Alignment(orig, cor)
  edits = alignment.get_rule_edits()

  edit_annotations = []
  for edit in edits:
    edit = classify(edit)
    edit_annotations.append((edit.type[2:], edit.o_str, edit.o_start, edit.o_end,  edit.c_str, edit.c_start, edit.c_end))

  orig_tokens = orig_text.split()
  ignore_indexes = []

  for edit_annotation in edit_annotations:
    edit_type = edit_annotation[0]
    edit_str_start = edit_annotation[1]
    edit_spos = edit_annotation[2]
    edit_epos = edit_annotation[3]
    edit_str_end = edit_annotation[4]
    print(edit_type, edit_str_start,  edit_spos, edit_epos, edit_str_end)
    for i in range(edit_spos+1, edit_epos):
      ignore_indexes.append(i)
    if edit_str_start == "":
        if edit_spos - 1 >= 0:
            new_edit_str = orig_tokens[edit_spos - 1]
            edit_spos -= 1
        else:
            new_edit_str = orig_tokens[edit_spos + 1]
            edit_spos += 1
        if edit_type == "PUNCT":
          st = "<a type='" + edit_type + "' edit='" + edit_str_end + "'>" + new_edit_str + "</a>"
        else:
          st = "<a type='" + edit_type + "' edit='" + new_edit_str + " " + edit_str_end + "'>" + new_edit_str + "</a>"
        orig_tokens[edit_spos] = st
    elif edit_str_end == "":
      st = "<d type='" + edit_type + "' edit=''>" + edit_str_start + "</d>"
      orig_tokens[edit_spos] = st
    else:
      st = "<c type='" + edit_type + "' edit='" + edit_str_end + "'>" + edit_str_start + "</c>"
      orig_tokens[edit_spos] = st

  for i in sorted(ignore_indexes, reverse=True):
    del(orig_tokens[i])

  result = " ".join(orig_tokens)

  return result

if __name__ == "__main__":
  handler()