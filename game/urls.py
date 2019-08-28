from django.conf.urls import url
from . import views

urlpatterns = [
    # Index
    url(r'^$', views.index_page, name='index'),

    # Game stuff
    url(r'^games/?$', views.play, name='play'),
    url(r'^games/(?P<game_id>[0-9]+)/?$', views.play, name='play'),
    url(r'^games/new/?$', views.new_game, name='new_game'),
    # Ajax move POST URL
    url(r'^ajax/post_move/?$', views.make_move, name='move'),

    # Word definition stuff
    url(r'^words/?$', views.word_list, name='words'),
    url(r'^words/(?P<word_name>[a-z]+)/?$', views.definition_list, name='word'),
    url(r'^send_word/?$', views.send_word, name='send_word'),

    # Account stuff
    url(r'^login/?$', views.login_page, name='login'),
    url(r'^register/?$', views.register, name='register'),
    url(r'^logout/?$', views.logout_page, name='logout'),

    # Profile stuff
    url(r'^users/(?P<username>[A-Za-z0-9_@+-. ]+)/?$', views.profile, name='profile'),
    url(r'^users/?$', views.userlist, name='userlist'),
    url(r'^users/(?P<username>[A-Za-z0-9_@+-. ]+)/edit/?$', views.edit_profile, name='edit_profile'),
    url(r'^users/(?P<username>[A-Za-z0-9_@+-. ]+)/challenge/?$', views.new_game, name='challenge'),
    url(r'^users/search/?$', views.user_search, name='user_search'),
]
