# django stuff
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404

# words stuff
from . import contextualize
from . import word_validation
from .board_util import get_tile_at, is_tile_at, do_board_move, draw_from_string, draw_from_list, draw2x7, find_full_word
from .dictionary_data import default_draw_pile, hat_pile

# models
from ..models import Game, GameState

# stdlib stuff
from datetime import datetime
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

    if is_p1:
        page_name += (" against %s" % game.player_2.username)
    elif viewable:
        # if not player 1, but in the game...
        page_name += (" against %s" % game.player_1.username)

    print(game.game_state.last_word_pos)
    context = {
        "page_name": page_name,
        "navbar": [ { "name": "home", "page": "index" },
                    { "name": "games", "page": "play" },
                  ],
        "game": game,
        "game_id": game_id,
        "game_state": game.game_state,
        "highlight_squares": ast.literal_eval(game.game_state.last_word_pos),
        "include_game_resources": viewable,
        "viewable": viewable,
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
        game.date_started = datetime.now()
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

        # Find words that intersect with the one you played
        intersecting_words = []
        for loc in move_locs:
            if loc[0] == -1:
                continue
            intersecting_words.append(find_full_word(new_board, loc[0], loc[1], not horizontal_word))

        # Validate words
        bad_words = []
        if not word_validation.validate(last_word_played):
            bad_words.append(last_word_played)
        for word in intersecting_words:
            if not word_validation.validate(word):
                if word not in bad_words:
                    bad_words.append(word)

        if len(bad_words) > 0:
            if len(bad_words) == 1:
                return HttpResponse("sorry, %s is not an acceptable word" % bad_words[0])
            elif len(bad_words) == 2:
                return HttpResponse("sorry, %s and %s are not acceptable words" % (bad_words[0], bad_words[1]))
            else:
                # gotta get that oxford comma
                return HttpResponse("sorry, %s, and %s are not acceptable words" % (", ".join(bad_words[:-1]), bad_words[-1]))

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
        else:
            game.game_state.p2_letters = letters
        game.game_state.draw_pile = draw_pile
        game.game_state.last_word_pos = repr(db_moves)
        game.game_state.last_word = last_word_played
        game.game_state.board = new_board
        game.game_state.save()
        game.someone_moved = True
        game.p1_turn = not game.p1_turn
        game.last_move = datetime.now()
        game.save()
        return HttpResponse("200" + game.game_state.board + "|" + letters)
    if request.method == "GET":
        return HttpResponse("hi, please send your AJAX requests via POST! thanks~")
