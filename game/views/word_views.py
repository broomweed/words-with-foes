from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound
from django.urls import reverse
from django.db.models import Count
from django.utils import timezone

from . import contextualize
from ..models import Game, Word, Definition

def definition_list(request, word_name=None):
    if word_name is None:
        raise Http404("no word provided!")
    try:
        word = Word.objects.get(name=word_name)
        definitions = Definition.objects.filter(word=word).order_by('-date_submitted')
        if len(definitions) == 0:
            definitions = None # no definitions - not sure if this is a thing that can happen,
                               # but maybe if a definition gets deleted or something
    except Word.DoesNotExist:
        definitions = None # word never defined
    context = {
        "navbar": [ { "page": "index", "name": "home" },
                    { "page": "words", "name": "words" },
                  ],
        "page_name": word_name.upper(),
        "word_name": word_name.upper(),
        "definitions": definitions,
    }
    contextualize(context, request)
    return render(request, 'game/definition.html', context)

def word_list(request):
    words = Word.objects.annotate(num_defs=Count('definition')).order_by('-last_updated')
    context = {
        "navbar": [ { "page": "index", "name": "home" },
                  ],
        "page_name": "words",
        "words": words,
    }
    contextualize(context, request)
    return render(request, 'game/words.html', context)

@login_required
def send_word(request):
    if 'word' not in request.POST or 'definition' not in request.POST or 'pos' not in request.POST:
        return HttpResponse("please provide a word, a part of speech, and a definition!")
    if 'game_id' not in request.POST:
        return HttpResponse("malformed request.")
    # validate to make sure they're sending data they're able to update
    game = Game.objects.get(id=request.POST['game_id'])
    if game.game_state.last_word != request.POST['word']:
        return HttpResponse("you cannot define that word!")
    if game.game_state.last_word_defined:
        return HttpResponse("you already defined that word!")
    word, created = Word.objects.get_or_create(name=request.POST['word'].lower())
    definition = Definition(word=word, text=request.POST['definition'], part_of_speech=request.POST['pos'])
    definition.submitter = request.user
    definition.save()
    word.last_updated = timezone.now()
    word.save()

    game.game_state.last_word_defined = True
    game.game_state.save()

    return HttpResponseRedirect(reverse('word', args=[word.name]))
