import random

def is_tile_at(board, x, y):
    return get_tile_at(board, x, y) != " " and get_tile_at(board, x, y) != "-"

def get_tile_at(board, x, y):
    print(type(board), type(x), type(y))
    return board[y*15+x]

def do_board_move(board, move):
    b_list = list(board)
    b_list[move[2]*15 + move[1]] = move[0]
    return "".join(b_list)

def draw_from_string(string):
    array = list(string) # string as a list
    new_pile, letter = draw_from_list(array)
    return "".join(new_pile), letter

def draw_from_list(array):
    if len(array) > 0:
        letter = array.pop(random.randint(0, len(array)-1))
        return array, letter # return new string and letter
    else:
        return [], "-" # no more letters!

def draw2x7(string):
    # Return two hands and a diminished draw pile, drawn in alternating order
    p1l = []
    p2l = []
    array = list(string) # get it as a list
    for i in range(0, 14):
        array, letter = draw_from_list(array)
        if i % 2 == 0:
            p1l.append(letter)
        else:
            p2l.append(letter)
    return "".join(array), "".join(p1l), "".join(p2l)

def find_full_word(board, x, y, is_horizontal):
    word_found = ""
    if not is_tile_at(board, x, y):
        return ""
    if is_horizontal:
        word_start = word_end = x
        y_pos = y
        while word_start > 0 and is_tile_at(board, word_start-1, y_pos):
            word_start -= 1
        while word_end < 14 and is_tile_at(board, word_end+1, y_pos):
            word_end += 1
        for i in range(word_start, word_end+1):
            word_found += get_tile_at(board, i, y_pos)
    else:
        word_start = word_end = y
        x_pos = x
        while word_start > 0 and is_tile_at(board, x_pos, word_start-1):
            word_start -= 1
        while word_end < 14 and is_tile_at(board, x_pos, word_end+1):
            word_end += 1
        for i in range(word_start, word_end+1):
            word_found += get_tile_at(board, x_pos, i)
    return word_found
