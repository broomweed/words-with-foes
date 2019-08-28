import json

transitions = {}

with open("english.txt") as wordfile:
    for word in wordfile:
        word = "*"+word.rstrip("\n")+"*"
        for pos in range(0, len(word)-2):
            key = word[pos:pos+2]
            val = word[pos+2]
            if key not in transitions:
                transitions[key] = []
            if val not in transitions[key]:
                transitions[key] += val

print(json.dumps(transitions))
