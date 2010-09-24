from bhoma.utils.couch.database import get_db
from django.http import HttpResponse
import json

class CouchPaginator(object):
    """
    Allows pagination of couchdbkit ViewResult objects.
    This class is meant to be used in conjunction with datatables.net
    ajax APIs, to allow you to paginate your views efficiently.
    """
    
    
    def __init__(self, view_name, generator_func, search=True): 
        """
        The generator function should be able to convert a couch 
        view results row into the appropriate json.
        
        No searching will be done unless you pass in a search view
        """
        self._view = view_name
        self._generator_func = generator_func
        self._search = search
        
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
        
        # search
        search_key = query.get("sSearch", "")
        if search_key:
            items = get_db().view(self._view, skip=start, limit=count, descending=desc, key=search_key.lower(), reduce=False)
            if start + len(items) < count:
                total_display_rows = len(items)
            else:
                total_display_rows = get_db().view(self._view, key=search_key.lower(), reduce=True).one()["value"]
                
        else:
            items = get_db().view(self._view, skip=start, limit=count, descending=desc, reduce=False)
            total_display_rows = items.total_rows
        
        # this startkey, endkey business is not currently used, 
        # but is a better way to search eventually.
        # for now the skip parameter is fast enough to suit our scale
        startkey, endkey = None, None
        all_json = []
        for row in items:
            if not startkey:
                startkey = row["key"]
            endkey = row["key"]
            all_json.append(self._generator_func(row))
        
        to_return = {"sEcho": query.get("sEcho", "0"),
                     "iTotalDisplayRecords": total_display_rows,
                     "iTotalRecords": items.total_rows,
                     "aaData": all_json}
        
        for key, val in extras.items():
            to_return[key] = val
        
        return HttpResponse(json.dumps(to_return))
                                                                        