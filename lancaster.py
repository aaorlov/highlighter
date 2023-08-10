import re

class LancasterStemmer:
    default_rule_tuple = (
        "ai*2.",  # -ia > -   if intact
        "a*1.",  # -a > -    if intact
        "bb1.",  # -bb > -b
        "city3s.",  # -ytic > -ys
        "ci2>",  # -ic > -
        "cn1t>",  # -nc > -nt
        "dd1.",  # -dd > -d
        "dei3y>",  # -ied > -y
        "deec2ss.",  # -ceed >", -cess
        "dee1.",  # -eed > -ee
        "de2>",  # -ed > -
        "dooh4>",  # -hood > -
        "e1>",  # -e > -
        "feil1v.",  # -lief > -liev
        "fi2>",  # -if > -
        "gni3>",  # -ing > -
        "gai3y.",  # -iag > -y
        "ga2>",  # -ag > -
        "gg1.",  # -gg > -g
        "ht*2.",  # -th > -   if intact
        "hsiug5ct.",  # -guish > -ct
        "hsi3>",  # -ish > -
        "i*1.",  # -i > -    if intact
        "i1y>",  # -i > -y
        "ji1d.",  # -ij > -id   --  see nois4j> & vis3j>
        "juf1s.",  # -fuj > -fus
        "ju1d.",  # -uj > -ud
        "jo1d.",  # -oj > -od
        "jeh1r.",  # -hej > -her
        "jrev1t.",  # -verj > -vert
        "jsim2t.",  # -misj > -mit
        "jn1d.",  # -nj > -nd
        "j1s.",  # -j > -s
        "lbaifi6.",  # -ifiabl > -
        "lbai4y.",  # -iabl > -y
        "lba3>",  # -abl > -
        "lbi3.",  # -ibl > -
        "lib2l>",  # -bil > -bl
        "lc1.",  # -cl > c
        "lufi4y.",  # -iful > -y
        "luf3>",  # -ful > -
        "lu2.",  # -ul > -
        "lai3>",  # -ial > -
        "lau3>",  # -ual > -
        "la2>",  # -al > -
        "ll1.",  # -ll > -l
        "mui3.",  # -ium > -
        "mu*2.",  # -um > -   if intact
        "msi3>",  # -ism > -
        "mm1.",  # -mm > -m
        "nois4j>",  # -sion > -j
        "noix4ct.",  # -xion > -ct
        "noi3>",  # -ion > -
        "nai3>",  # -ian > -
        "na2>",  # -an > -
        "nee0.",  # protect  -een
        "ne2>",  # -en > -
        "nn1.",  # -nn > -n
        "pihs4>",  # -ship > -
        "pp1.",  # -pp > -p
        "re2>",  # -er > -
        "rae0.",  # protect  -ear
        "ra2.",  # -ar > -
        "ro2>",  # -or > -
        "ru2>",  # -ur > -
        "rr1.",  # -rr > -r
        "rt1>",  # -tr > -t
        "rei3y>",  # -ier > -y
        "sei3y>",  # -ies > -y
        "sis2.",  # -sis > -s
        "si2>",  # -is > -
        "ssen4>",  # -ness > -
        "ss0.",  # protect  -ss
        "suo3>",  # -ous > -
        "su*2.",  # -us > -   if intact
        "s*1>",  # -s > -    if intact
        "s0.",  # -s > -s
        "tacilp4y.",  # -plicat > -ply
        "ta2>",  # -at > -
        "tnem4>",  # -ment > -
        "tne3>",  # -ent > -
        "tna3>",  # -ant > -
        "tpir2b.",  # -ript > -rib
        "tpro2b.",  # -orpt > -orb
        "tcud1.",  # -duct > -duc
        "tpmus2.",  # -sumpt > -sum
        "tpec2iv.",  # -cept > -ceiv
        "tulo2v.",  # -olut > -olv
        "tsis0.",  # protect  -sist
        "tsi3>",  # -ist > -
        "tt1.",  # -tt > -t
        "uqi3.",  # -iqu > -
        "ugo1.",  # -ogu > -og
        "vis3j>",  # -siv > -j
        "vie0.",  # protect  -eiv
        "vi2>",  # -iv > -
        "ylb1>",  # -bly > -bl
        "yli3y>",  # -ily > -y
        "ylp0.",  # protect  -ply
        "yl2>",  # -ly > -
        "ygo1.",  # -ogy > -og
        "yhp1.",  # -phy > -ph
        "ymo1.",  # -omy > -om
        "ypo1.",  # -opy > -op
        "yti3>",  # -ity > -
        "yte3>",  # -ety > -
        "ytl2.",  # -lty > -l
        "yrtsi5.",  # -istry > -
        "yra3>",  # -ary > -
        "yro3>",  # -ory > -
        "yfi3.",  # -ify > -
        "ycn2t>",  # -ncy > -nt
        "yca3>",  # -acy > -
        "zi2>",  # -iz > -
        "zy1s.",  # -yz > -ys
    )

    def __init__(self, rule_tuple=None, strip_prefix_flag=False):
        self.rule_dictionary = {}
        self._strip_prefix = strip_prefix_flag
        self._rule_tuple = rule_tuple if rule_tuple else self.default_rule_tuple

    def parseRules(self, rule_tuple=None):
        rule_tuple = rule_tuple if rule_tuple else self._rule_tuple
        valid_rule = re.compile("^[a-z]+\*?\d[a-z]*[>\.]?$")
        self.rule_dictionary = {}
        for rule in rule_tuple:
            if not valid_rule.match(rule):
                raise ValueError("The rule {0} is invalid".format(rule))
            first_letter = rule[0:1]
            if first_letter in self.rule_dictionary:
                self.rule_dictionary[first_letter].append(rule)
            else:
                self.rule_dictionary[first_letter] = [rule]

    def stem(self, word):
        word = word.lower()
        word = self.__stripPrefix(word) if self._strip_prefix else word
        intact_word = word
        if not self.rule_dictionary:
            self.parseRules()
        return self.__doStemming(word, intact_word)

    def __doStemming(self, word, intact_word):
        valid_rule = re.compile("^([a-z]+)(\*?)(\d)([a-z]*)([>\.]?)$")
        proceed = True
        while proceed:
            last_letter_position = self.__getLastLetter(word)
            if (last_letter_position < 0 or word[last_letter_position] not in self.rule_dictionary):
                proceed = False
            else:
                rule_was_applied = False
                for rule in self.rule_dictionary[word[last_letter_position]]:
                    rule_match = valid_rule.match(rule)
                    if rule_match:
                        (
                            ending_string,
                            intact_flag,
                            remove_total,
                            append_string,
                            cont_flag,
                        ) = rule_match.groups()
                        remove_total = int(remove_total)
                        if word.endswith(ending_string[::-1]):
                            if intact_flag:
                                if word == intact_word and self.__isAcceptable(word, remove_total):
                                    word = self.__applyRule(word, remove_total, append_string)
                                    rule_was_applied = True
                                    if cont_flag == ".":
                                        proceed = False
                                    break
                            elif self.__isAcceptable(word, remove_total):
                                word = self.__applyRule(word, remove_total, append_string)
                                rule_was_applied = True
                                if cont_flag == ".":
                                    proceed = False
                                break
                if rule_was_applied == False:
                    proceed = False
        return word

    def __getLastLetter(self, word):
        last_letter = -1
        for position in range(len(word)):
            if word[position].isalpha():
                last_letter = position
            else:
                break
        return last_letter

    def __isAcceptable(self, word, remove_total):
        word_is_acceptable = False
        if word[0] in "aeiouy":
            if len(word) - remove_total >= 2:
                word_is_acceptable = True
        elif len(word) - remove_total >= 3:
            if word[1] in "aeiouy":
                word_is_acceptable = True
            elif word[2] in "aeiouy":
                word_is_acceptable = True
        return word_is_acceptable

    def __applyRule(self, word, remove_total, append_string):
        new_word_length = len(word) - remove_total
        word = word[0:new_word_length]
        if append_string:
            word += append_string
        return word

    def __stripPrefix(self, word):
        for prefix in (
            "kilo",
            "micro",
            "milli",
            "intra",
            "ultra",
            "mega",
            "nano",
            "pico",
            "pseudo",
        ):
            if word.startswith(prefix):
                return word[len(prefix) :]
        return word

    def __repr__(self):
        return "<LancasterStemmer>"