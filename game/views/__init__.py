colors = [
    ("red", "#ff6f4f"),
    ("purple", "#db4aff"),
    ("yellow", "#ffff3a"),
    ("blue", "#45caff"),
    ("green", "#baf872"),
    ("tan", "#f3d782"),
]

def index_page(request):
    context = { "page_name": "home" }
    contextualize(context, request)
    return render(request, 'game/index.html', context)

# Set up context stuff the same in each page
def contextualize(context, request):
    context['logged_in'] = request.user.is_authenticated
    context['user'] = request.user
    context['colors'] = colors
    context['symbol'] = "x3b2"
    context['symbol_alt'] = 'beta'
    context['symbol_color'] = '#777'

from .account_views import *
from .game_views import *
from .word_views import *
