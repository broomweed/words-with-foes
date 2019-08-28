import json

# Real words that aren't accepted.
print ("[words-with-enemies] parsing dictionary...")
with open("game/dict/english.txt") as word_file:
    dictionary = set(word.strip().lower() for word in word_file)

# The 2nd-order Markov chain for validating words.
print ("[words-with-enemies] parsing transition file...")
with open("game/dict/transitions.txt") as transitions_file:
    transitions = json.load(transitions_file)

print ("[words-with-enemies] ready.")

# How many points each letter is worth.
scores = {
    '*':  0,
    'A':  1,
    'B':  3,
    'C':  3,
    'D':  2,
    'E':  1,
    'F':  4,
    'G':  2,
    'H':  4,
    'I':  1,
    'J':  8,
    'K':  5,
    'L':  1,
    'M':  3,
    'N':  1,
    'O':  1,
    'P':  3,
    'Q':  10,
    'R':  1,
    'S':  1,
    'T':  1,
    'U':  1,
    'V':  4,
    'W':  4,
    'X':  8,
    'Y':  4,
    'Z':  10,
};

# Locations of bonus squares.
bonus = {
    (7, 7): "c",
    (3, 0): "tw",
    (2, 1): "dl",
    (1, 2): "dl",
    (0, 3): "tw",
    (6, 0): "tl",
    (8, 0): "tl",
    (5, 1): "dw",
    (9, 1): "dw",
    (4, 2): "dl",
    (10,2): "dl",
    (3, 3): "tl",
    (3, 7): "dw",
    (4, 6): "dl",
    (5, 5): "tl",
    (6, 4): "dl",
}

# Quantities of each letter in the game.
default_draw_pile = ""\
    +"A"*9	\
    +"B"*2	\
    +"C"*2	\
    +"D"*4	\
    +"E"*12	\
    +"F"*2	\
    +"G"*3	\
    +"H"*2	\
    +"I"*9	\
    +"J"*1	\
    +"K"*1	\
    +"L"*4	\
    +"M"*2	\
    +"N"*6	\
    +"O"*8	\
    +"P"*2	\
    +"Q"*1	\
    +"R"*6	\
    +"S"*4	\
    +"T"*6	\
    +"U"*4	\
    +"V"*2	\
    +"W"*2	\
    +"X"*1	\
    +"Y"*2	\
    +"Z"*1	\
    +"*"*2

# The hat-mode draw pile...
hat_pile = "H"*33+"A"*33+"T"*33+"V"*1
