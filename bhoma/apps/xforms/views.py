from dimagi.utils.web import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from bhoma.apps.xforms.models.couch import CXFormInstance
from django.views.decorators.http import require_POST
import touchforms.formplayer.views as formplayer_views
from bhoma.apps.xforms.util import post_xform_to_couch
from collections import defaultdict
from couchexport.export import export, Format
from StringIO import StringIO

def xform_list(request):
    return formplayer_views.xform_list(request)

def xform_data(request, instance_id):
    instance = CXFormInstance.get(instance_id)
    return render_to_response(request, "xforms/single_instance_raw.html", 
                              {"instance": instance})
    

def download(request, xform_id):
    """
    Download an xform
    """
    return formplayer_views.download(request, xform_id)
    
def download_excel(request):
    """
    Download all data for an xform
    """
    namespace = request.GET.get("xmlns", "")
    if not namespace:
        raise Exception("You must specify a namespace to download!")
    tmp = StringIO()
    
    format = request.GET.get("format", Format.XLS_2007)
    
    if export(namespace, tmp, format):
        response = HttpResponse(mimetype='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=%s.%s' % (namespace.split('/')[-1], format)  
        response.write(tmp.getvalue())
        tmp.close()
        return response
    else:
        return HttpResponse("Sorry, there was no data found for the namespace '%s'." % namespace)

def play(request, xform_id, callback=None, preloader_data={}):
    """
    Play an XForm.
    
    If you specify callback, instead of returning a response this view
    will call back to your method upon completion (POST).  This allows
    you to call the view from your own view, but specify a callback
    method afterwards to do custom processing and responding.
    
    The callback method should have the following signature:
        response = <method>(xform, document)
    where:
        xform = the django model of the form 
        document = the couch object created by the instance data
        response = a valid http response
    """
    def inner_callback(xform, instance):
        # post to couch
        doc = post_xform_to_couch(instance)
        # call the callback, if there, otherwise route back to the 
        # xforms list
        if callback:
            return callback(xform, doc)
        else:
            return HttpResponseRedirect(reverse("xform_list"))
    
    keyargs = {}
    def get_patient_id(preload_data):
        if "case" in preload_data and "patient_id" in preload_data["case"]:
            return preload_data["case"]["patient_id"]
    pat_id = get_patient_id(preloader_data)
    
    if pat_id:
        keyargs["abort_callback"] = lambda *args, **kwargs: \
                HttpResponseRedirect(reverse("single_patient", args=[pat_id])) 
        
    return formplayer_views.play(request, xform_id, inner_callback, preloader_data, 
                                 input_mode="type", 
                                 force_template="bhoma_touchscreen.html",
                                 **keyargs)

def player_proxy(request):
    """Proxy to an xform player, to avoid cross-site scripting issues"""
    return formplayer_views.player_proxy(request)
    
@require_POST
def post(request, callback=None):
    """
    XForms can get posted here.  They will be forwarded to couch.
    
    Just like play, if you specify a callback you get called, 
    otherwise you get a generic response.  Callbacks follow
    a different signature as play, only passing in the document
    (since we don't know what xform was being posted to)
    """
    # just forward the post request to couch
    # this won't currently work with ODK
    
    # post to couch
    instance = request.raw_post_data
    doc = post_xform_to_couch(instance)
    if callback:
        return callback(doc)
    return HttpResponse("Thanks! Your new xform id is: %s" % doc["_id"])
