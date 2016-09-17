var board = []

var letters = []
var move = []
var id_about_to_place = -1;

var load_letters = true;

var scores = { '*': 0, 'A':  1, 'B':  3, 'C':  3, 'D':  2, 'E':  1, 'F':  4, 'G':  2, 'H':  4, 'I':  1, 'J':  8, 'K':  5, 'L':  1, 'M':  3, 'N':  1, 'O':  1, 'P':  3, 'Q':  10, 'R':  1, 'S':  1, 'T':  1, 'U':  1, 'V':  4, 'W':  4, 'X':  8, 'Y':  4, 'Z':  10 };

var bonus = [ [7, 7, "c"], [3, 0, "tw"], [2, 1, "dl"], [1, 2, "dl"], [0, 3, "tw"], [6, 0, "tl"], [8, 0, "tl"], [5, 1, "dw"], [9, 1, "dw"], [4, 2, "dl"], [10, 2, "dl"], [3, 3, "tl"], [3, 7, "dw"], [4, 6, "dl"], [5, 5, "tl"], [6, 4, "dl"] ];

var error = '';

function init () {
    board_string = board_string.replace(/-/g, " ")
    for (var i = 0; i < 15; i++) {
        board[i] = [];
        for (var j = 0; j < 15; j++) {
            board[i][j] = board_string.charAt(i*15 + j)
        }
    }

    if (letters.length == 0 || load_letters) {
        for (var i = 0; i < 7; i++) {
            var l = letters_string.charAt(i)
            letters += l;
        }
        load_letters = false;
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
                if (highlight_squares && point_highlighted(col, row)) {
                    board_text += "<span class='tile oldtile last'>" + board[row][col] + score_char(board[row][col]) + "</span>";
                } else {
                    board_text += "<span class='tile oldtile'>" + board[row][col] + score_char(board[row][col]) + "</span>";
                }
            }
        }
        board_text += "<br />";
    }
    board_text += "<br />{";
    for (var p = 0; p < 7; p++) {
        var letter_found = false
        for (var l in letters) {
            if (move[l][0] == -1 && move[l][1] == p) {
                if (letters[l] == "-" || letters[l] == " ") {
                    letter_found = false;
                } else {
                    if (id_about_to_place == l) {
                        board_text += "<span class='tile newtile selected'><a href='#' onclick='select(-1)'><b>"+letters[l]+"</b>" + score_char(letters[l]) + "</a></span>";
                    } else {
                        board_text += "<span class='tile newtile'><a href='#' onclick='select("+l+")'><b>"+letters[l]+"</b>" + score_char(letters[l]) + "</a></span>";
                    }
                    letter_found = true;
                }
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
    board_text += "<br /><br />";
    if (moved_pieces > 0) {
        board_text += " <a href='#' onclick='recall_all()'>&#8634; recall</a>";
    } else {
        board_text += " &#8634; recall";
    }
    board_text += " <a href='#' onclick='shuffle()'>&#8605; shuffle</a> ";
    var can_play = false;
    for (var m in move) {
        if (move[m][0] != -1) {
            can_play = true;
            break;
        }
    }
    if (can_play) {
        board_text += "<a href='#' onclick='send_move()'>";
    }
    board_text += "&#x2713; send move"
    if (can_play) {
        board_text += "</a>";
    }
    if (error != "") {
        board_text += "<br /><br />"+error;
    }
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
    var value = scores[chara.toUpperCase()];
    if (value == undefined) {
        return "?";
    }
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
    /* No validity checking on this end -- put tiles anywhere */
    //var is_valid = valid_position(x, y);
    //if (is_valid) {
    board[y][x] = tile;
    render();
    console.log("Ok.");
    //}
}

/*function valid_position(x, y) {
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
}*/

window.onload = function() {
    init();
    render();
}

var httpRequest;

function move_response() {
    if (httpRequest.readyState === XMLHttpRequest.DONE) {
        if (httpRequest.status == 200) {
            if (httpRequest.responseText.match(/200/)) {
                response = httpRequest.responseText.replace(/200/, '');
                board_string = response.split("|")[0];
                letters = response.split("|")[1];
                load_letters = true;
                init();
                window.location.reload(true);
            } else {
                error = httpRequest.responseText.replace(/\n/g, "<br />");
            }
            render();
        } else {
            alert("There was a problem: " + httpRequest.responseText);
        }
    }
}

function send_move() {
    httpRequest = new XMLHttpRequest();
    if (!httpRequest) {
        alert("couldn't send move due to a strange error.\nperhaps your browser is too old?");
        return false;
    }

    httpRequest.onreadystatechange = move_response;
    url = 'http://localhost:8000/ajax/post_move/';
    httpRequest.open('POST', url, true);
    var csrftoken = get_cookie('csrftoken');
    if (sameOrigin(url)) {
        // Send the token to same-origin, relative URLs only.
        // Send the token only if the method warrants CSRF protection
        // Using the CSRFToken value acquired earlier
        httpRequest.setRequestHeader("X-CSRFToken", csrftoken);
    } else {
        alert("something went wrong! it's possible your request was compromised!");
    }
    httpRequest.setRequestHeader("Cache-Control", "no-cache");
    moveData = '[';
    for (m in move) {
        // construct JSON!
        moveData += '["' + letters[m] + '",' + move[m][0] + ',' + move[m][1] + '],';
    }
    moveData = moveData.substr(0, moveData.length-1) + ']'; // chop off last comma
    moveData = '{ "moves": ' + moveData + ', "id": ' + game_id + ' }';
    console.log(moveData)
    httpRequest.send(moveData);
}

function get_cookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i in cookies) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}

function point_highlighted(x, y) {
    for (index in highlight_squares) {
        if (highlight_squares[index][0] == x && highlight_squares[index][1] == y) {
            return true;
        }
    }
    return false;
}
