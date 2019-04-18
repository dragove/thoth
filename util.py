import ahocorasick

A = ahocorasick.Automaton()

dirties = []
with open('dirty.txt', 'r') as f:
    words = f.readlines()
    for word in words:
        dirties.append(word.replace('\n', ''))

for idx, key in enumerate(dirties):
    A.add_word(key, (idx, key))

A.make_automaton()


# check whether the sentence has dirty words. If so, this function will return True, otherwise, return False.
def check_dirty(sentence):
    for item in A.iter(sentence):
        return True
    return False

