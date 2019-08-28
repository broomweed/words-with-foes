from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.urls import reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render

from . import contextualize

from ..models import Definition

def login_page(request):
    if request.user.is_authenticated:
        context = {
            "page_name": "log in???",
            "navbar": [ { "name": "home", "page": "index" } ],
            "already_logged_in": True
        }
        contextualize(context, request)
        return render(request, 'game/login.html', context)
    if request.method == 'GET':
        next = None
        if request.GET.get('next'):
            next = request.GET.get('next')
        context = {
            "page_name": "log in",
            "navbar": [ { "name": "home", "page": "index" } ],
            "next": next,
        }
        contextualize(context, request)
        return render(request, 'game/login.html', context)
    elif request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('pass', '')
        errors = []
        # Handle '?next=/blah'
        next_page = ''
        if request.GET:
            next_page = request.GET['next']
        # Handle empty boxes
        if username == '':
            errors.append('please enter your username!')
        if password == '':
            errors.append('please enter your password!')
        if len(errors) == 2:
            # if both these errors occurred simultaneously
            errors = ['please fill out this form before clicking the button!']
        if len(errors) == 0:
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if next_page != '':
                    return HttpResponseRedirect(next_page)
                else:
                    return HttpResponseRedirect(reverse('index'))
            else:
                # fail!
                errors.append("sorry, your username and password didn't match.")
        context = {
            "page_name": "log in",
            "navbar": [ { "name": "home", "page": "index" } ],
            "errors": errors,
        }
        contextualize(context, request)
        return render(request, 'game/login.html', context)

def register(request):
    if request.user.is_authenticated:
        context = {
            "page_name": "register...?",
            "navbar": [ { "name": "home", "page": "index" } ],
            "already_logged_in": True
        }
        contextualize(context, request)
        return render(request, 'game/login.html', context)
    if request.method == 'GET':
        context = {
            "page_name": "register",
            "navbar": [ { "name": "home", "page": "index" } ],
        }
        contextualize(context, request)
        return render(request, 'game/register.html', context)
    elif request.method == 'POST':
        errors = []
        username = request.POST.get('username', '')
        password = request.POST.get('pass', '')
        password_confirm = request.POST.get('pass2', '')
        email = request.POST.get('email', '')
        email_confirm = request.POST.get('email2', '')
        fav_color = request.POST.get('favcolor', '')
        if username == "":
            errors.append("please enter a username!")
        if password == "" and password_confirm == "":
            errors.append("please enter a password!")
        elif password == "" or password_confirm == "":
            errors.append("please enter your password twice, just in case.")
        elif password != password_confirm:
            errors.append("your passwords didn't match.")
        if email == "" and email_confirm == "":
            errors.append("please enter your email!")
        elif email == "" or email_confirm == "":
            errors.append("please enter your email twice, because this is a thing we do.")
        elif email != email_confirm:
            errors.append("your emails didn't match.")
        elif "@" not in email or "." not in email:
            errors.append("that doesn't look like an email to me.")
        if fav_color == "":
            errors.append("please select a favorite color!")
        if len(username) > 30:
            errors.append("please limit your username to 30 characters.")
        if username == "" and email == "" and email_confirm == "" \
                and password == "" and password_confirm == "" and fav_color == "":
            errors = ["please fill out this form before clicking the button."]
        if len(errors) > 0:
            context = {
                "page_name": "register",
                "navbar": [ { "name": "home", "page": "index" } ],
                "errors": errors,
            }
            contextualize(context, request)
            return render(request, 'game/register.html', context)
        else:
            try:
                user = User.objects.create_user(username, email, password)
            except IntegrityError:
                context = {
                    "page_name": "register",
                    "navbar": [ { "name": "home", "page": "index" } ],
                    "errors": [ "there's already a user with that name! :(" ],
                }
                contextualize(context, request)
                return render(request, 'game/register.html', context)

            user.profile.fav_color = fav_color
            user.profile.save()

            context = {
                "page_name": "success!",
                "navbar": [ { "name": "home", "page": "index" },
                            { "name": "register", "page": "register" }
                ],
                "new_user": username,
                "color": user.profile.fav_color,
            }
            contextualize(context, request)
            return render(request, 'game/register_success.html', context)

def logout_page(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))

def profile(request, username=None):
    if username is None:
        return Http404("no user name provided!")
    user = User.objects.get(username=username)
    defs = Definition.objects.filter(submitter=user)
    context = { "page_name": user.username,
                "navbar": [ { "name": "home", "page": "index" },
                            { "name": "users", "page": "userlist" },
                          ],
                "viewed": user,
                "defs": defs,
                #"datejoined": str("{dt:%b} {dt.day} {dt.year}").format(dt=user.date_joined),
                #"lastseen": str("{dt:%b} {dt.day} {dt.year}").format(dt=user.last_login),
                "datejoined": user.date_joined,
                "lastseen": user.last_login
              }
    contextualize(context, request)
    return render(request, 'game/profile.html', context)

def userlist(request):
    users = User.objects.all().order_by('-date_joined')
    context = {
        "page_name": "users",
        "navbar": [ { "name": "home", "page": "index" } ],
        "users": users,
    }
    contextualize(context, request)
    return render(request, 'game/user_list.html', context)

@login_required
def edit_profile(request, username=None):
    if request.method == 'GET':
        viewed_user = User.objects.get(username=username)
        context = {
            "page_name": "edit profile",
            "navbar": [ { "name": "home", "page": "index" },
                        { "name": "users", "page": "userlist" },
                        { "name": username, "page": "profile", "arg": username },
                      ],
            "viewed": viewed_user,
        }
        contextualize(context, request)
        return render(request, 'game/edit_profile.html', context)
    if request.method == 'POST':
        # change profile but DON'T do it unless admin or the names match
        context = {
            "page_name": "edit profile",
            "navbar": [ { "name": "home", "page": "index" },
                        { "name": "users", "page": "userlist" },
                        { "name": username, "page": "profile", "arg": username },
                      ],
        }
        contextualize(context, request)
        if username == request.user.username or request.user.is_staff:
            try:
                viewed_user = User.objects.get(username=username)
            except DoesNotExist:
                raise Http404("no user named %s" % username)
            context['viewed'] = viewed_user
            errors = []
            if request.POST.get('pass'):
                if request.POST.get('pass') == request.POST.get('pass2'):
                    viewed_user.set_password(request.POST.get('pass'))
                else:
                    errors.append("your passwords didn't match!")
            if request.POST.get('email'):
                viewed_user.email = request.POST.get('email')
            if request.POST.get('favcolor'):
                viewed_user.profile.fav_color = request.POST.get('favcolor')
            if request.POST.get('bio'):
                viewed_user.profile.bio = request.POST.get('bio')
            if len(errors) == 0:
                viewed_user.save()
                viewed_user.profile.save()
                context['msg'] = "profile saved successfully!"
                return render(request, 'game/edit_profile.html', context)
            else:
                context['errors'] = errors
                return render(request, 'game/edit_profile.html', context)
            return HttpResponse("hi what's up")

        else:
            return HttpResponseForbidden("you aren't allowed to edit other people's profiles!")

def user_search(request, term):
    pass
