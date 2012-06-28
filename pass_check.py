import copy, re, collections
import word_list
import cProfile

class Part(object):
    def __init__(self, word, type=None, mutations=None):
        if mutations is None: mutations = []
        if not isinstance(mutations, list): mutations = [mutations]
        self.word = word
        self.type = type
        self.mutations = mutations

class Mutation(object):
    def __init__(self, type, index):
        self.type = type
        self.index = index

    def __repr__(self):
        return "{}: {}".format(self.type, self.index)

class Password(object):
    SYMBOLS = list('`~!@#$%^&*()-_=+[{]}\\|;:\'",<.>/?')
    DELIMITERS = list('/\\-. _=+&')
    LEET = {
        '4':['a'],
        '@':['a'],
        '8':['b'],
        '(':['c'],
        '3':['e'],
        '9':['g'],
        '#':['h'],
        '!':['i'],
        '1':['l'],
        '0':['o'],
        '2':['r'],
        '5':['s'],
        '$':['s'],
        '7':['t'],
        '%':['z']}
    COST = {}
    regexContainsLetters = re.compile(r"[a-zA-Z]")
    regexIsDate = re.compile(r"(\d{1,4})([-/_. ])?(\d{1,2})\2?(\d{1,4})?$")
    regexIsYMD = re.compile(r"(\d{2,4})[-/_. ]?(\d{1,2})[-/_. ]?(\d{1,2})$")
    regexIsMDY = re.compile(r"(\d{1,2})[-/_. ]?(\d{1,2})[-/_. ]?(\d{2,4})$")
    regexIsMY = re.compile(r"(\d{1,2})[-/_. ]?(\d{2,4})$")
    regexIsYM = re.compile(r"(\d{2,4})[-/_. ]?(\d{1,2})$")
    regexIsY = re.compile(r"^(19[4-9][0-9]|(20)?[0-2][0-9])$")

    def __init__(self, password):
        self.password = password
        self.parts = [Part(password)]

    def subPermutations(self, word, minLength=4):
        """Generates all possible substrings, from longest to shortest.
        minLength of 2:
        words   [:]
        word    [0:4]
        ords    [1:5]
        wor     [0:3]
        ord     [1:4]
        rds     [2:5]
        wo      [0:2]
        or      [1:3]
        rd      [2:4]
        ds      [3:5]
        """
        length = len(word)
        endRange = length - minLength + 2
        for i in range(0, endRange):
            start = -1
            end = length-i
            for j in range(0, i):
                start += 1
                end += 1
                yield (word[:start], word[end:], word[start:end])

    def removeDelimiter(self, word):
        """Search for a delimiter between each character.
        Returns an array of changes and the modified string."""
        # word: "p-a-s-s-w-o-r-d"
        # word: "-p-a-s-s-2008"
        # word: "---$-$---@%"
        # check first character for delimiter
        # if found, check
        word = list(word)
        if word[0] in Password.DELIMITERS:
            for i in range(0, len(word)+1, 2):
                pass
        elif word[1] in Password.DELIMITERS:
            pass


    def removeLeet(self, word):
        """Removes common letter and number/symbol substitutions.
        Can function as a generator, in case there is more than one
        possible result (functionality is currently disabled for performance).

        Returns a tuple: (number of replacements made, word)."""

        result = [[]]
        replaced = []
        for index, char in enumerate(list(word)):
            # Special exception for multiple un-leet choices:
            if char in self.LEET and len(self.LEET[char]) > 1:
                result += copy.deepcopy(result)
                for resultSub in result[:len(result)/2]:
                    resultSub.append(self.LEET[char][0])
                for resultSub in result[len(result)/2:]:
                    resultSub.append(self.LEET[char][1])
                replaced.append(index)
                continue

            elif char in self.LEET:
                char = self.LEET[char][0]
                replaced.append(index)

            for resultSub in result:
                resultSub.append(char)

        for temp in result:
            yield replaced, ''.join(temp)

    def removeCase(self, word):
        """Returns an index of all uppercase letters, and the word in
        lowercase."""
        replaced = [index for index, char in enumerate(word) if char.isupper()]
        return replaced, word.lower()

    def searchDictionary(self, word):
        """Ask word_list to find the word, and return the number of records
        searched, or False if not found."""
        return word_list.findWord(word)

    def findWord(self, part = 0):
        """Removes and saves mutations, then attempts to find the largest
        dictionary word (larger than two characters) within the given part
        index."""

        # TODO: Performance: find a way to reduce the number of searches

        word = self.parts[part].word
        mutations = []
        for prefix, suffix, sub in self.subPermutations(word, minLength=3):
            replaced, sub = self.removeCase(sub)
            if replaced:
                mutations = [(Mutation('case', replaced))]

            for replaced, sub in self.removeLeet(sub):
                if self.searchDictionary(sub):
                    if replaced:
                        mutations.append(Mutation('leet', replaced))
                    # Replace part, indicate that it is a word
                    return self.addParts(
                        part, prefix, suffix, sub, "word", mutations)
        return False

    def isYear(self, num):
        if (1940 <= num <= 2020) or (40 <= num <= 99) or (0 <= num <= 20):
            return True
        return False

    def isDate(self, place1, place2, place3):
        """Return a date type if a date is valid, False if not. Day, Month, and
        Year can be in any order. Does not currently check for valid days
        depending on length of month."""
        if not place2 and not place3:
            # Y only
            if self.isYear(place1):
                return 'date-common-Y'
        elif not place3:
            # MD or YM
            if (1 <= place1 <= 12 and 1 <= place2 <= 31) or (
                1 <= place2 <= 12 and 1 <= place1 <= 31):
                return 'date-common-MD'
            elif (1 <= place1 <= 12 and self.isYear(place2)) or (
                1 <= place2 <= 12 and self.isYear(place1)):
                return 'date-common-YM'
        else:
            # YMD
            if self.isYear(place1):
                if (1 <= place2 <= 12 and 1 <= place3 <= 31) or (
                    1 <= place3 <= 12 and 1 <= place2 <= 31):
                    return 'date-common-YMD'
            # Have to check both for dates such as 01/04/01
            if self.isYear(place1):
                if (1 <= place1 <= 12 and 1 <= place2 <= 31) or (
                    1 <= place2 <= 12 and 1 <= place1 <= 31):
                    return 'date-common-YMD'
        return False

    def addParts(self, part, prefix, suffix, sub, type, mutations=None):
        self.parts[part] = Part(sub, type, mutations)
        if suffix:
            self.parts.insert(part + 1, Part(suffix))
        if prefix:
            self.parts.insert(part, Part(prefix))
        return True

    def findDate(self, part = 0):
        """Search for a date in any possible format.
        Performs a general regex for date formats, then validates digits."""
        word = self.parts[part].word
        for prefix, suffix, sub in self.subPermutations(word, minLength=4):
            if re.search(Password.regexContainsLetters, sub):
                continue

            result = re.match(
                r"(\d{1,4})([-/_. ])?(\d{1,4})?\2?(\d{1,4})?$", sub)
            if result:
                # Not sure what's a month, day, or year - let isDate decide
                places = (
                    result.group(1),
                    result.group(3),
                    result.group(4))
                places = [int(x) if x is not None else None for x in places]
                type = self.isDate(places[0], places[1], places[2])
                if not type:
                    return False
                return self.addParts(
                    part, prefix, suffix, sub, type)
        return False

    def findRepeated(self, part):
        """Finds repeated characters."""
        word = self.parts[part].word
        if len(collections.Counter(word)) > len(word) - 1:
            return False

        for prefix, suffix, sub in self.subPermutations(word, minLength=2):
            if len(collections.Counter(sub)) == 1:
                return self.addParts(part, prefix, suffix, sub, 'repetition')
            elif len(collections.Counter(sub.lower())) == 1:
                replaced, word = self.removeCase(word)
                return self.addParts(part, prefix, suffix, sub, 'repetition',
                              Mutation('case', replaced))
        return False

    def findKeyGraph(self, part):
        """Finds common runs on the keyboard."""


def main():
    #pw = Password("((!11!No!5))01/49")
    #pw = Password("08-31-2004")
    #pw = Password("((substrings))$$$$are2008/10/22tricky")
    pw = Password("<<notG00dP4$$word>>tim2008-08")

    # Strictly done this way for testing
    changed = 1
    while changed:
        changed = 0
        for part in range(0, len(pw.parts)):
            if pw.parts[part].type:
                continue
            if pw.findDate(part):
                changed = 1
                continue
            if pw.findWord(part):
                changed = 1
                continue
            if pw.findRepeated(part):
                changed = 1
                continue

    for part in pw.parts:
        if part.type:
            print "Found part '{}', type '{}', with mutations '{}'".format(
                part.word, part.type, part.mutations)
        else:
            print "Found part '{}'".format(part.word)

if __name__ == "__main__":
    cProfile.run('main()')
    #main()
