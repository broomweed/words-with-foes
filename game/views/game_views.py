# django stuff
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

# words stuff
from . import contextualize
from . import word_validation
from .board_util import get_tile_at, is_tile_at, do_board_move, draw_from_string, draw_from_list, draw2x7, find_full_word
from .dictionary_data import default_draw_pile, hat_pile, scores, bonus

# models
from ..models import Game, GameState

# stdlib stuff
import json
import ast


@login_required
def play(request, game_id=None):
    if game_id is None:
        return game_index(request)

    game = get_object_or_404(Game, pk=game_id)
    viewable = False
    is_player = False
    is_p1 = False
    if game.player_2.username == request.user.username:
        viewable = True # but not player 1
        is_player = True
    if game.player_1.username == request.user.username:
        is_p1 = True
        viewable = True
        is_player = True
    if game.public:
        viewable = True
        # (if not p1 or p2 and game isn't public, can't view game)
    page_name = "game #%d" % int(game_id)

    your_turn = False
    opponent = "doofus"
    if is_p1:
        page_name += (" against %s" % game.player_2.username)
        opponent = game.player_2
        if game.p1_turn:
            your_turn = True
    elif is_player:
        # if not player 1, but in the game...
        page_name += (" against %s" % game.player_1.username)
        opponent = game.player_1
        if not game.p1_turn:
            your_turn = True

    context = {
        "page_name": page_name,
        "navbar": [ { "name": "home", "page": "index" },
                    { "name": "games", "page": "play" },
                  ],
        "game": game,
        "game_id": game_id,
        "game_state": game.game_state,
        "highlight_squares": ast.literal_eval(game.game_state.last_move_pos),
        "include_game_resources": viewable,
        "viewable": viewable,
        "your_turn": your_turn,
        "opponent": opponent,
        "is_p1": is_p1,
    }
    contextualize(context, request)
    return render(request, 'game/play.html', context)

@login_required
def game_index(request):
    # N.B.: Player 1 is always the user who created the game, regardless of whether they go first or not.
    p1_games = Game.objects.filter(player_1=request.user)
    p2_games = Game.objects.filter(player_2=request.user)

    # Your games are:  - games where someone moved where it's your turn
    #                  - games where someone hasn't moved where someone let you make the first move
    #                    (ie you're player 2, and player 2 makes the first move)
    your_games = (((p1_games.filter(p1_turn=True) | p2_games.filter(p1_turn=False)) \
              .exclude(someone_moved=False)) | (p2_games.filter(someone_moved=False, p2_first=True))).order_by('last_move')

    # Their games are: - games where someone moved where it's your turn
    #                  - games where someone hasn't moved where you let them make the first move
    #                    (ie you're player 1, and you let player 2 make the first move)
    their_games = (((p1_games.filter(p1_turn=False) | p2_games.filter(p1_turn=True)) \
              .exclude(someone_moved=False)) | (p1_games.filter(someone_moved=False, p2_first=True))).order_by('last_move')

    # 'Challenges' (referred to publicly as 'unfinished business') are games you've started but not played in yet
    challenges = p1_games.filter(someone_moved=False, p1_turn=True).order_by('date_started')
    context = {
        "page_name": "games",
        "navbar": [ { "name": "home", "page": "index" } ],
        "your_games": your_games,
        "their_games": their_games,
        "challenges": challenges,
    }
    contextualize(context, request)
    return render(request, 'game/game_list.html', context)

@login_required
def new_game(request, username):
    if request.method == "GET":
        user = User.objects.get(username=username)
        context = { "challenged": user,
                    "navbar": [ { "name": "home", "page": "index" },
                                { "name": "users", "page": "userlist" },
                                { "name": username, "page": "profile", "arg": username },
                              ],
                    "page_name": "challenge",
        }
        contextualize(context, request)
        return render(request, 'game/challenge.html', context)
    if request.method == "POST":
        if username == request.user.username:
            return HttpResponse("you can't start a game with yourself!")
        opponent = User.objects.get(username=username)
        game = Game()
        game.player_1 = request.user
        game.player_2 = opponent
        game.public = request.POST.get('public', False)
        game.p2_first = bool(request.POST.get('go_second', False))
        if game.p2_first:
            game.p1_turn = False
        else:
            game.p1_turn = True
        game.someone_moved = False
        state = GameState()
        state.board=" "*225
        if request.POST.get("hat"):
            state.draw_pile, state.p1_letters, state.p2_letters = draw2x7(hat_pile)
        else:
            state.draw_pile, state.p1_letters, state.p2_letters = draw2x7(default_draw_pile)
        state.save()
        game.game_state = state
        game.completed = False
        game.date_started = timezone.now()
        game.last_move = game.date_started
        game.save()
        return HttpResponseRedirect(reverse('play', args=[game.id]))

@login_required
def make_move(request):
    if request.method == "POST":
        ajax_string = request.body.decode(encoding='UTF-8')
        data = json.loads(ajax_string)
        # DIFFERENT ERRORS THAT CAN HAPPEN
        # Syntax error
        if 'moves' not in data or 'id' not in data:
            return HttpResponse("malformed request :(\n(you must send data in the proper JSON format.)")
        # Trying to play in a game that doesn't exist, or trying to play in a game that you aren't a player in
        try:
            game = Game.objects.get(id=data['id'])
        except Game.DoesNotExist:
            return HttpResponseNotFound("no game with id #%d!" % data['id'])
        is_p1 = False
        if game.player_1 == request.user:
            is_p1 = True
        elif game.player_2 != request.user:
            return HttpResponseForbidden("you, " + request.user.username +", are not a player in this game!")
        # Trying to play out of turn
        if (is_p1 and not game.p1_turn) or (not is_p1 and game.p1_turn):
            return HttpResponseForbidden("it is not your turn!")
        # Wacky cheating-type moves (playing too many tiles, no tiles, wrong tiles, etc.)
        moves_made = data['moves']
        if len(moves_made) != 7:
            return HttpResponse("malformed request :(\n(you must send exactly 7 tile positions.\nuse -1 as x-position for unused ones.)")
        tiles_played = 0
        for loc in moves_made:
            if loc[1] != -1:
                tiles_played += 1
        if tiles_played == 0:
            # TODO: implement PASSING
            return HttpResponse("malformed request :(\n(you must play at least one tile!)")
        if is_p1:
            # TODO: this is wrong, you can play a bunch of copies of a letter you have
            for move in moves_made:
                if move[0] not in game.game_state.p1_letters:
                    return HttpResponse("malformed request :(\n(you must only play letters you have!)")
        else:
            for move in moves_made:
                if move[0] not in game.game_state.p2_letters:
                    return HttpResponse("malformed request :(\n(you must only play letters you have!)")
        # Illegal moves
        x_positions = {}
        y_positions = {}
        move_locs = [] # just the locations, no letters
        for loc in moves_made:
            if loc[1] != -1:
                if loc[1] not in x_positions:
                    x_positions[loc[1]] = loc[2]
                if loc[2] not in y_positions:
                    y_positions[loc[2]] = loc[1]
                move_locs.append([loc[1], loc[2]])
        if len(x_positions.keys()) > 1 and len(y_positions.keys()) > 1:
            # if more than one x-position and more than one y-position, can't be a legal move...
            return HttpResponse("invalid move position.")
        if not game.someone_moved:
            if tiles_played < 2:
                return HttpResponse("you must play more than one tile on the first move!")
        horizontal_word = False
        if tiles_played > 1:
            if len(y_positions.keys()) == 1:
                horizontal_word = True
        else:
            # if only one tile played, it could get a little weird
            if is_tile_at(game.game_state.board, move_locs[0][0]-1, move_locs[0][1]) \
                    or is_tile_at(game.game_state.board, move_locs[0][0]+1, move_locs[0][1]):
                horizontal_word = True
        # if there are gaps (actual empty spots on the board) in the move, can't be a legal move
        # so we find the start and end of the word (horizontally or vertically) and iterate through looking
        # for a blank spot
        word_start = -1
        word_end = -1
        if horizontal_word:
            word_start = min(x_positions.keys())
            word_end = max(x_positions.keys())
            for i in range(word_start, word_end+1):
                if not is_tile_at(game.game_state.board, i, x_positions[word_start]) and [i, x_positions[word_start]] not in move_locs:
                    return HttpResponse("invalid move position.")
        else:
            word_start = min(y_positions.keys())
            word_end = max(y_positions.keys())
            for i in range(word_start, word_end+1):
                if not is_tile_at(game.game_state.board, y_positions[word_start], i) and [y_positions[word_start], i] not in move_locs:
                    return HttpResponse("invalid move position.")
        if game.someone_moved:
            # if this isn't the first move, tiles being placed must be adjacent to preexisting tiles
            # (but not on top of them, obviously)
            move_adjacent = False
            for i in move_locs:
                if is_tile_at(game.game_state.board, i[0], i[1]):
                    return HttpResponse("malformed request :(\n(you can't play a tile on top of another tile!)")
                if (i[0] < 14 and is_tile_at(game.game_state.board, i[0]+1, i[1])) or (i[0] > 0 and is_tile_at(game.game_state.board, i[0]-1, i[1])) \
                        or (i[1] > 0 and is_tile_at(game.game_state.board, i[0], i[1]-1)) or (i[1] < 14 and is_tile_at(game.game_state.board, i[0], i[1]+1)):
                    break
            else:
                return HttpResponse("tiles must be played adjacent to preexisting tiles!")
        else:
            if [7, 7] not in move_locs:
                return HttpResponse("you must play in the center on your first move!")

        # if the move survived all that.......then it's a valid move! (but not necessarily a valid word)
        # Make actual move, and calculate which tile indices need to be replaced from draw pile (moved_tiles)
        new_board = game.game_state.board
        unmoved_tiles = []
        for m in moves_made:
            if m[1] == -1:
                unmoved_tiles.append(m[2])
                continue
            new_board = do_board_move(new_board, m)

        moved_tiles = []
        for pos in range(0, 7):
            if pos not in unmoved_tiles:
                moved_tiles.append(pos)

        # Calculate "full" word that was played (consecutive letters aligned with new tiles)
        last_word_played = find_full_word(new_board, move_locs[0][0], move_locs[0][1], horizontal_word)

        # Calculate bonus score
        bonus_points = 0
        multiplier = 1
        for move in moves_made:
            if move[1] == -1:
                continue
            print("< %s : %d >" % (move[0], scores[move[0]]))
            bonus_type = bonus.get( (move[1], move[2]) ) or bonus.get( (move[1], 14-move[2]) ) \
                      or bonus.get( (14-move[2], move[1]) ) or bonus.get( (14-move[2], 14-move[1]) )
            if bonus_type == None or bonus_type == "c":
                continue
            if bonus_type == "tw":
                print("triple word!")
                multiplier *= 3
            if bonus_type == "dw":
                print("double word!")
                multiplier *= 2
            if bonus_type == "tl":
                print("triple letter!")
                bonus_points += 2*scores[move[0]]
            if bonus_type == "dl":
                print("double letter!")
                bonus_points += scores[move[0]]

        print("mult: %d, pts: %d" % (multiplier, bonus_points))

        # Find words that intersect with the one you played
        intersecting_words = []
        for loc in move_locs:
            if loc[0] == -1:
                continue
            intersecting_words.append(find_full_word(new_board, loc[0], loc[1], not horizontal_word))

        # Validate words
        all_words = [last_word_played]
        all_words += intersecting_words
        bad_words = []
        real_words = []

        for word in all_words:
            result = word_validation.validate(word)
            if result == 0:
                continue
            if result == 1 and word not in real_words:
                # in dictionary
                real_words.append(word)
            if result == 2 and word not in bad_words:
                # unpronounceable
                bad_words.append(word)

        error_string = ""
        if len(bad_words) > 0:
            if len(bad_words) == 1:
                error_string += "%s doesn't look like a word!\n" % bad_words[0]
            elif len(bad_words) == 2:
                error_string += "%s and %s don't look like words!\n" % (bad_words[0], bad_words[1])
            else:
                # gotta get that oxford comma
                error_string += "%s, and %s don't look like words!\n" % (", ".join(bad_words[:-1]), bad_words[-1])
        if len(real_words) > 0:
            if len(real_words) == 1:
                error_string += "%s is a real word!\n" % real_words[0]
            elif len(real_words) == 2:
                error_string += "%s and %s are real words!\n" % (real_words[0], real_words[1])
            else:
                error_string += "%s, and %s are real words!\n" % (", ".join(real_words[:-1]), real_words[-1])

        if len(error_string) > 0:
            return HttpResponse(error_string)

        # If all words were valid, then score words
        move_score = 0
        for letter in last_word_played:
            move_score += scores[letter]
        move_score = (move_score + bonus_points) * multiplier
        for word in intersecting_words:
            if len(word) == 1:
                # don't score 1-letter 'words'
                continue
            for letter in word:
                move_score += scores[letter]

        # Store most recent move in DB, for highlighting newly-played tiles
        db_moves = []
        for i in move_locs:
            db_moves.append( (i[0], i[1]) )

        # Draw new letters from the draw pile
        letters = []
        draw_pile = game.game_state.draw_pile
        for pos in range(0, 7):
            if pos in moved_tiles:
                # returns two values: new draw pile and letter drawn
                draw_pile, letter = draw_from_string(draw_pile)
                letters.append(letter)
            else:
                letters.append(moves_made[pos][0])
        letters = "".join(letters)

        # Put everything back in the database now
        if is_p1:
            game.game_state.p1_letters = letters
            game.game_state.p1_score += move_score
        else:
            game.game_state.p2_letters = letters
            game.game_state.p2_score += move_score
        game.game_state.last_move_score = move_score
        game.game_state.draw_pile = draw_pile
        game.game_state.last_move_pos = repr(db_moves)
        game.game_state.last_word = last_word_played
        game.game_state.board = new_board
        game.game_state.last_word_defined = False
        game.game_state.save()
        game.someone_moved = True
        game.p1_turn = not game.p1_turn
        game.last_move = timezone.now()
        game.save()
        return HttpResponse("200" + game.game_state.board + "|" + letters)
    if request.method == "GET":
        return HttpResponse("hi, please send your AJAX requests via POST! thanks~")
