

class DesignDoc(object):
    """Data structure representing a design doc"""
    
    def __init__(self, database, id):
        self.id = id
        self._doc = database.get(id)
        self.name = id.replace("_design/", "")
    
    @property
    def views(self):
        views = []
        if "views" in self._doc:
            for view_name, _ in self._doc["views"].items(): 
                views.append(view_name)
        return views
    

def get_db():
    """
    Get the bhoma database.  
    """
    # this is a bit of a hack, since it assumes all the models talk to the same
    # db.  that said a lot of our code relies on that assumption.
    # this import is here because of annoying dependencies
    from bhoma.apps.patient.models import CPatient
    return CPatient.get_db()

def get_design_docs(database):
    design_doc_rows = database.view("_all_docs", startkey="_design/", 
                                    endkey="_design/zzzz")
    ret = []
    for row in design_doc_rows:
        ret.append(DesignDoc(database, row["id"]))
    return ret

def get_view_names(database):
    design_docs = get_design_docs(database)
    views = []
    for doc in design_docs:
        for view_name in doc.views:
            views.append("%s/%s" % (doc.name, view_name))
    return views