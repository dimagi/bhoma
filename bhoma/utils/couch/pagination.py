from bhoma.utils.couch.database import get_db
from django.http import HttpResponse
import json

class CouchPaginator(object):
    """
    Allows pagination of couchdbkit ViewResult objects.
    This class is meant to be used in conjunction with datatables.net
    ajax APIs, to allow you to paginate your views efficiently.
    """
    
    
    def __init__(self, view_name, generator_func):
        """
        The generator function should be able to convert a couch 
        view results row into the appropriate json.
        """
        self._view = view_name
        self._generator_func = generator_func
        
    def get_ajax_response(self, request, default_display_length="10", 
                          default_start="0", extras={}):
        """
        From a datatables generated ajax request, return the appropriate
        httpresponse containing the appropriate objects objects.
        
        Extras allows you to override any individual paramater that gets 
        returned
        """
        query = request.POST if request.method == "POST" else request.GET
        
        count = int(query.get("iDisplayLength", default_display_length));
        
        start = int(query.get("iDisplayStart", default_start));
        
        # sorting
        desc_str = query.get("sSortDir_0", "desc")
        desc = desc_str == "desc"
        
        items = get_db().view(self._view, skip=start, limit=count, descending=desc)
        startkey, endkey = None, None
        all_json = []
        for row in items:
            if not startkey:
                startkey = row["key"]
            endkey = row["key"]
            all_json.append(self._generator_func(row))
        
        to_return = {"sEcho": query.get("sEcho", "0"),
                     "iTotalDisplayRecords": items.total_rows,
                     "aaData": all_json}
        
        for key, val in extras.items():
            to_return[key] = val
        
        return HttpResponse(json.dumps(to_return))
                                                                        