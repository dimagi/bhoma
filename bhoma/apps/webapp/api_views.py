from django.http import HttpResponseRedirect, HttpResponse
import json
from django.views.decorators.http import require_POST
from django.core.urlresolvers import reverse
from django.contrib.auth.models import check_password, User
from bhoma.apps.profile.models import BhomaUserProfile
from bhoma.utils.logging import log_exception

def get_usernames(request):
    """
    Gets a list of usernames for the login workflow
    """
    users = BhomaUserProfile.objects.filter(is_web_user=True).values_list('user__username', flat=True).order_by('user__username')
    # json doesn't like unicode markups
    users = [str(usr) for usr in users]
    return HttpResponse(json.dumps(users))
    

@require_POST
def authenticate_user(request):
    """
    Perform django authentication on a user/password
    """
    username = request.POST["username"]
    password = request.POST["password"]
    user = User.objects.get(username=username)
    # HACK: try to authenticate first with the normal password, then with the lowercase password
    success = check_password(password, user.password) or check_password(password.lower(), user.password)
    return HttpResponse(json.dumps({"result": success}))
    
def user_exists(request):
    """
    Gets a list of usernames for the login workflow
    """
    username = request.POST["username"]
    exists = User.objects.filter(username__iexact=username).exists()
    return HttpResponse(json.dumps({"result": exists}))
