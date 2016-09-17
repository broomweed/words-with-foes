var board = []

var letters = []
var move = []
var id_about_to_place = -1;

var scores = { '*': 0, 'A':  1, 'B':  3, 'C':  3, 'D':  2, 'E':  1, 'F':  4, 'G':  2, 'H':  4, 'I':  1, 'J':  8, 'K':  5, 'L':  1, 'M':  3, 'N':  1, 'O':  1, 'P':  3, 'Q':  10, 'R':  1, 'S':  1, 'T':  1, 'U':  1, 'V':  4, 'W':  4, 'X':  8, 'Y':  4, 'Z':  10 };

var bonus = [ [7, 7, "c"], [3, 0, "tw"], [2, 1, "dl"], [1, 2, "dl"], [0, 3, "tw"], [6, 0, "tl"], [8, 0, "tl"], [5, 1, "dw"], [9, 1, "dw"], [4, 2, "dl"], [10, 2, "dl"], [3, 3, "tl"], [3, 7, "dw"], [4, 6, "dl"], [5, 5, "tl"], [6, 4, "dl"] ];

function init () {
    for (var i = 0; i < 15; i++) {
        board[i] = [];
        for (var j = 0; j < 15; j++) {
            board[i][j] = ' ';
        }
    }

    var alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ*";
    for (var i = 0; i < 7; i++) {
        var l = alphabet.charAt(Math.floor(Math.random() * alphabet.length));
        letters += l;
    }

    for (var i = 0; i < 7; i++) {
        move[i] = [-1, i];
    }
}

function render() {
    var board_space = document.getElementById("board");
    var board_text = "";
    board_text += "<tt>";
    for (var row in board) {
        board_text += "&nbsp;&nbsp;";
        for (var col in board[row]) {
            if (board[row][col] == ' ') {
                var move_here = false;
                for (var m in move) {
                    if (move[m] != null && move[m][0] == col && move[m][1] == row) {
                        if (id_about_to_place != m) {
                            board_text += "<span class='tile newtile'><a href='#' onclick='select("+m+")'><b>"+letters[m] + "</b>" + score_char(letters[m]) + "</a></span>";
                        } else {
                            board_text += "<span class='tile newtile selected'><a href='#' onclick='select(-1)'><b>"+letters[m]+"</b>" + score_char(letters[m]) + "</a></span>";
                        }
                        move_here = true;
                    }
                }
                if (!move_here) {
                    var bonus_here = "";
                    for (var i in bonus) {
                        if ((bonus[i][0] == col && bonus[i][1] == row)
                            || (14-bonus[i][0] == col && 14-bonus[i][1] == row)
                            || (14-bonus[i][0] == row && bonus[i][1] == col)
                            || (bonus[i][0] == row && 14-bonus[i][1] == col)) {
                            bonus_here = bonus[i][2];
                        }
                    }
                    if (bonus_here != "") {
                        if (bonus_here != "c") {
                            bonus_display = bonus_here.replace("l", "&#x1D38;").replace("w", "&#x1D42;").replace("d", "2").replace("t", "3");
                            board_text += "<span class='tile bonus'><span class='"+bonus_here+"'><a href='#' id='"+col+","+row+"' class='place'>"+bonus_display+"</a></span></span>";
                        } else {
                            board_text += "<span class='tile bonus center'><a href='#' id='"+col+","+row+"' class='place'>&#x207A;&#x208A;</a></span>";
                        }
                    } else {
                        board_text += "<span class='tile off'><a href='#' id='"+col+","+row+"' class='place'>&nbsp;&nbsp;</a></span>";
                    }
                }
            } else {
                board_text += "<span class='tile oldtile'>" + board[row][col] + score_char(board[row][col]) + "</span>";
            }
        }
        board_text += "<br />";
    }
    board_text += "<br />{";
    for (var p = 0; p < 7; p++) {
        var letter_found = false
        for (var l in letters) {
            if (move[l][0] == -1 && move[l][1] == p) {
                if (id_about_to_place == l) {
                    board_text += "<span class='tile newtile selected'><a href='#' onclick='select(-1)'><b>"+letters[l]+"</b>" + score_char(letters[l]) + "</a></span>";
                } else {
                    board_text += "<span class='tile newtile'><a href='#' onclick='select("+l+")'><b>"+letters[l]+"</b>" + score_char(letters[l]) + "</a></span>";
                }
                letter_found = true;
            }
        }
        if (!letter_found) {
            /*if (id_about_to_place == l) {
              board_text += "<span class='tile return'><a href='#' onclick='recall("+l+")'><b>" + letters[l] + "</b>&#x2193;</a></span>";
              } else {*/
            board_text += "<span class='nottile'><a href='#' onclick='recall("+p+")'>__</a></span>";
            //}
        }
    }
    board_text += "}";
    var moved_pieces = 0;
    for (var i = 0; i < move.length; i++) {
        if (move[i][0] != -1) {
            moved_pieces++;
        }
    }
    if (moved_pieces > 0) {
        board_text += " <a href='#' onclick='recall_all()'>&#8634; recall</a>";
    } else {
        board_text += " &#8634; recall";
    }
    board_text += " <a href='#' onclick='shuffle()'>&#8605; shuffle</a>";
    board_text += "</tt>";
    board_space.innerHTML = board_text;
    setPlaceFunction();
}

function setPlaceFunction() {
    var place_links = document.getElementsByClassName('place');
    for (var link in place_links) {
        place_links[link].onclick = (function(pass_id) { return function() {
            if (id_about_to_place != -1) {
                var x = parseInt(pass_id.split(",")[0]);
                var y = parseInt(pass_id.split(",")[1]);
                //place_tile(x, y, letters[id_about_to_place]);
                move[id_about_to_place] = [x, y];
                id_about_to_place = -1;
                render();
            } else {
                console.log("You must select a tile first!");
            }
        } })(place_links[link].id);
    }
}

function recall_all() {
    // find open slots
    var open_slots = [];
    for (var i = 0; i < 7; i++) {
        slot_open = true;
        for (var m in move) {
            if(move[m][0] == -1 && move[m][1] == i) {
                slot_open = false;
            }
        }
        if (slot_open) {
            open_slots.push(i);
        }
    }
    console.log("open slots: ", open_slots);
    for (m in move) {
        if (move[m][0] != -1) {
            move[m] = [-1, open_slots[0]];
            open_slots.shift();
        }
    }
    id_about_to_place = -1;
    render();
}

function recall(pos) {
    if (id_about_to_place == -1) {
        return;
    }
    move[id_about_to_place] = [-1, pos];
    id_about_to_place = -1
    render();
}

function shuffle() {
    // shuffle only tiles in tray
    id_about_to_place = -1;
    var new_order = shuffleArray([0,1,2,3,4,5,6]);
    var new_letters = [];
    var new_move = [];
    for (var i = 0; i < 7; i++) {
        if (move[i][0] == -1) {
            move[i][1] = new_order[i];
        }
    }
    render();
}

// per http://stackoverflow.com/questions/2450954/how-to-randomize-shuffle-a-javascript-array
function shuffleArray(array) {
    for (var i = array.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var temp = array[i];
        array[i] = array[j];
        array[j] = temp;
    }
    return array;
}

function select(tile_id) {
    id_about_to_place = tile_id;
    render();
}

function score_char(chara) {
    var value = scores[chara];
    if (value == 10) {
        value = '93';
    } else {
        value = '8' + value;
    }
    return '&#x20' + value + ';';
}

function place_tile(x, y, tile) {
    console.log('place tile '+tile+' at '+x+', '+y);
    if (tile.length > 1) {
        console.log("What.");
        return;
    }
    /* No validity checking on this end -- put tiles anywhere, check move legality later */
    //var is_valid = valid_position(x, y);
    //if (is_valid) {
    board[y][x] = tile;
    render();
    console.log("Ok.");
    //}
}

function valid_position(x, y) {
    if ((y > 0 && board[y-1][x] != " ")
            || (y < board.length-1 && board[y+1][x] != " ")
            || (x > 0 && board[y][x-1] != " ")
            || (x < board[0].length-1 && board[y][x+1] != " ") // if at least one adjacent tile is occupied...
            || (x == (board.length-1)/2 && y == (board.length-1)/2)) {  // or the center (always a valid move)
        if (board[y][x] == " ") {
            return true;
        }
    }
    return false;
}

window.onload = function() {
    init();
    render();
}
