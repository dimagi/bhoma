from datetime import datetime
from dimagi.utils.web import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from bhoma.apps.chw.models import CommunityHealthWorker,\
    get_django_user_object
from bhoma.apps.chw.forms import CHWForm
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import permission_required

def list_chws(request):
    """
    List chws
    """
    chws = CommunityHealthWorker.view("chw/by_clinic", include_docs=True)
    return render_to_response(request, "chw/chw_list.html",
                              {"chws": chws})
                               
def single(request, chw_id):
    """
    Single CHW
    """
    chw = CommunityHealthWorker.get(chw_id)
    return render_to_response(request, "chw/single_chw.html", 
                              {"chw": chw }) 
                               
@permission_required("superuser")
@require_POST
def delete(request, chw_id):
    """
    Delete a CHW
    """
    chw = CommunityHealthWorker.get(chw_id)
    name = chw.formatted_name
    if chw.user == request.user:
        messages.error(request, "You can't delete the logged in user!")
    else:
        if chw.user:
            chw.user.delete()
        chw.delete()
        messages.success(request, "User %s has been deleted." % name)
    return HttpResponseRedirect(reverse("manage_chws"))
    
@permission_required("superuser")
@require_POST
def deactivate(request, chw_id):
    """
    Deactivate a CHW
    """
    return _set_activation_status(request, chw_id, False)
    
@permission_required("superuser")
@require_POST
def activate(request, chw_id):
    """
    Activate a CHW
    """
    return _set_activation_status(request, chw_id, True)

def _set_activation_status(request, chw_id, status):
    chw = CommunityHealthWorker.get(chw_id)
    display = "activate" if status else "deactivate"
    if chw.user == request.user:
        messages.error(request, "You can't %s the logged in user!" % display)
    elif chw.user:
        chw.user.is_active = status
        chw.user.save()
        messages.success(request, "User %s has been %sd." % (chw.formatted_name, display))
    else:
        messages.info(request, "There was no %sd account found for %s so nothing was done." % (display, chw.formatted_name))
    return HttpResponseRedirect(reverse("manage_chws"))
    

def new(request):
    """
    Create a new CHW
    """
    if request.method == "POST":
        form = CHWForm(request.POST)
        if form.is_valid():
            all_clinic_ids= [form.cleaned_data["current_clinic"].slug]
            chw = CommunityHealthWorker(username=form.cleaned_data["username"],
                                        password=form.cleaned_data["password"],
                                        created_on=datetime.utcnow(),
                                        first_name=form.cleaned_data["first_name"],
                                        last_name=form.cleaned_data["last_name"],
                                        gender=form.cleaned_data["gender"],
                                        current_clinic_id=form.cleaned_data["current_clinic"].slug,
                                        current_clinic_zone=int(form.cleaned_data["current_clinic_zone"]),
                                        clinic_ids=all_clinic_ids)
            
            user = get_django_user_object(chw)
            
            if user.username != chw.username:
                chw.username = user.username
            chw.save()
            
            user.save()
            user.get_profile().chw_id=chw.get_id
            # prevent them from logging in / showing up on the main screen
            user.get_profile().is_web_user=False 
            user.save()
            messages.success(request, "User %s has been created." % chw.formatted_name)
            return HttpResponseRedirect(reverse("manage_chws"))  
    else:
        form = CHWForm()
        
    return render_to_response(request, "chw/new_chw.html", 
                              {"form": form})
                               
                                

