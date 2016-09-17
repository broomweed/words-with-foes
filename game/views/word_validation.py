from .board_util import get_tile_at, is_tile_at
from .dictionary_data import dictionary, transitions

def validate(string):
    string = string.lower()

    if len(string) == 1:
        # 1-letter "words" are always OK
        return True

    if string in dictionary:
        return False

    # Avoid words without vowels
    for let in ['a', 'e', 'i', 'o', 'u', 'y']:
        if let in string:
            break
    else:
        return False

    # if passed basic checks, make sure word is 'pronounceable'
    border_string = "*" + string + "*"
    # check each three-letter triplet to make sure it makes sense
    for val_index in range(0, len(border_string)-2): # up to third-to-last char
        key_string = border_string[val_index] + border_string[val_index+1]
        val_string = border_string[val_index+2]
        if key_string not in transitions:
            return False
        if val_string not in transitions[key_string]:
            return False

    return True

def validate_board(board):
    working_word = []
    improper_words = []
    # Validate words horizontally first
    for row in range(0, 15):
        for col in range(0, 15):
            if not is_tile_at(board, col, row):
                if len(working_word) > 0:
                    if not validate("".join(working_word)):
                        improper_words.append("".join(working_word))
                    working_word = []
            else:
                working_word.append(get_tile_at(board, col, row))

    # finish with one last check jic
    if len(working_word) > 0:
        if not validate("".join(working_word)):
            improper_words.append("".join(working_word))
    working_word = []

    # Validate words vertically
    # which is, uh, the exact same thing with row/col swapped
    for col in range(0, 15):
        for row in range(0, 15):
            if not is_tile_at(board, col, row):
                if len(working_word) > 0:
                    if not validate("".join(working_word)):
                        improper_words.append("".join(working_word))
                    working_word = []
            else:
                working_word.append(get_tile_at(board, col, row))

    # check once more at the end
    if len(working_word) > 0:
        if not validate("".join(working_word)):
            improper_words.append("".join(working_word))

    return improper_words
