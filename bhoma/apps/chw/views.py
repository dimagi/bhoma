from bhoma.utils.render_to_response import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from bhoma.apps.chw.models.couch import CommunityHealthWorker,\
    get_django_user_object
from bhoma.apps.chw.forms import CHWForm

def list(request):
    """
    List chws
    """
    chws = CommunityHealthWorker.view("chw/all")
    return render_to_response(request, "chw/chw_list.html",
                              {"chws": chws})
                               
def single(request, chw_id):
    """
    Single CHW
    """
    chw = CommunityHealthWorker.view("chw/all", key=chw_id).one()
    return render_to_response(request, "chw/single_chw.html", 
                              {"chw": chw})
    

def new(request):
    """
    Create a new CHW
    """
    if request.method == "POST":
        form = CHWForm(request.POST)
        if form.is_valid():
            # TODO: phones=form.cleaned_data["phones"],
            chw = CommunityHealthWorker(username=form.cleaned_data["username"],
                                        password=form.cleaned_data["password"],
                                        first_name=form.cleaned_data["first_name"],
                                        last_name=form.cleaned_data["last_name"],
                                        gender=form.cleaned_data["gender"],
                                        chw_id=form.cleaned_data["chw_id"],
                                        clinic_ids=[clinic.slug for clinic in form.cleaned_data["clinics"]])
            chw.save()
            user = get_django_user_object(chw)
            user.save()
            user.get_profile().chw_id=chw.get_id
            user.save()
            return HttpResponseRedirect(reverse("single_chw", args=[chw._id]))  
    else:
        form = CHWForm()
        
    return render_to_response(request, "chw/new_chw.html", 
                              {"form": form})
                               
                                

