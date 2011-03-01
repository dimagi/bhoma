from bhoma.apps.export.export import export_excel
from django.http import HttpResponse
from StringIO import StringIO


def download_model(request):
    """
    Download all data for a couchdbkit model
    """
    model_name = request.GET.get("model", "")
    if not model_name:
        raise Exception("You must specify a model to download!")
    tmp = StringIO()
    if export_excel(model_name, 'export/model', tmp, include_docs=True):
        response = HttpResponse(mimetype='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=%s.xls' % model_name
        response.write(tmp.getvalue())
        tmp.close()
        return response
    else:
        return HttpResponse("Sorry, there was no data found for the model '%s'." % model_name)

