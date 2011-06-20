from datetime import datetime
from dimagi.utils.web import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from bhoma.apps.chw.models import CommunityHealthWorker,\
    new_django_user_object
from bhoma.apps.chw.forms import CHWForm
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import permission_required
from bhoma.decorators import aggregation_required
from bhoma import const

@permission_required("superuser")
def list_chws(request):
    """
    List chws
    """
    chws = CommunityHealthWorker.view("chw/by_clinic", include_docs=True)
    return render_to_response(request, "chw/chw_list.html",
                              {"chws": chws})

                               
@permission_required("superuser")
def single(request, chw_id):
    """
    Single CHW
    """
    chw = CommunityHealthWorker.get(chw_id)
    return render_to_response(request, "chw/single_chw.html", 
                              {"chw": chw }) 
                               
@permission_required("superuser")
@require_POST
@aggregation_required([const.LOCATION_TYPE_NATIONAL , const.LOCATION_TYPE_PROVINCE])
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
@aggregation_required([const.LOCATION_TYPE_NATIONAL , const.LOCATION_TYPE_PROVINCE])
def deactivate(request, chw_id):
    """
    Deactivate a CHW
    """
    return _set_activation_status(request, chw_id, False)
    
@permission_required("superuser")
@require_POST
@aggregation_required([const.LOCATION_TYPE_NATIONAL , const.LOCATION_TYPE_PROVINCE])
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
    
@permission_required("superuser")
@aggregation_required([const.LOCATION_TYPE_NATIONAL , const.LOCATION_TYPE_PROVINCE])
def new_or_edit(request, chw_id=None):
    """
    Create a new CHW
    """
    if request.method == "POST":
        form = CHWForm(data=request.POST)
        if form.is_valid():
            edit_mode = bool(form.cleaned_data["id"])
            if edit_mode:
                chw = CommunityHealthWorker.get(form.cleaned_data["id"])
            else:
                chw = CommunityHealthWorker()
                chw.created_on = datetime.utcnow()
            
            all_clinic_ids= [form.cleaned_data["current_clinic"].slug]
            chw.username = form.cleaned_data["username"]
            chw.password = form.cleaned_data["password"]
            chw.first_name = form.cleaned_data["first_name"]
            chw.last_name = form.cleaned_data["last_name"]
            chw.gender = form.cleaned_data["gender"]
            chw.current_clinic_id = form.cleaned_data["current_clinic"].slug
            chw.current_clinic_zone = int(form.cleaned_data["current_clinic_zone"])
            chw.clinic_ids = all_clinic_ids
            
            if not edit_mode:
                user = new_django_user_object(chw)
                
                if user.username != chw.username:
                    chw.username = user.username
            chw.save()
            if not edit_mode:
                user.save()
                user.get_profile().chw_id=chw.get_id
                # prevent them from logging in / showing up on the main screen
                user.get_profile().is_web_user=False 
                user.save()
                messages.success(request, "User %s has been created." % chw.formatted_name)
            else:
                messages.success(request, "User %s has been updated." % chw.formatted_name)
            
            return HttpResponseRedirect(reverse("manage_chws"))
            
    else:
        if chw_id:
            form = CHWForm.from_instance(CommunityHealthWorker.get(chw_id))
        else:
            form = CHWForm()

    return render_to_response(request, "chw/new_chw.html", 
                              {"form": form})
                               
                                

