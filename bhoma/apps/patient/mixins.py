from dimagi.utils.couch import uid
from dimagi.utils.couch.database import get_db

class CouchCopyableMixin(object):
    """Mixin to add a copy method to an object for couch."""
    
    @classmethod
    def copy(cls, instance):
        """
        Create a backup copy of a instance object, returning the id of the 
        newly created document
        """
        instance_json = instance.to_json()
        backup_id = uid.new()
        instance_json["_id"] = backup_id 
        instance_json.pop("_rev")
        get_db().save_doc(instance_json)
        return backup_id
                

class PatientQueryMixin(object):
    """Mixin that add query methods with patient bolted on"""

    # we have to explicity have this property here or couchdbkit gets mad 
    # Couchdbkit does a lot of magic/validation about what properties
    # you want to add and by default assumes that everything should be
    # pushed to couch.  This allows you to define a list of semi-dynamic
    # properties that don't have this functionality
    
    # TODO: there has to be a saner way to do this
    patient = None
    
    @classmethod
    def __view_with_patient(cls, view_name, **params):
        def _patient_wrapper(row):
            """
            The wrapper bolts the patient object onto the case, if we find
            it, otherwise does what the view would have done in the first
            place and adds an empty patient property
            """
            from bhoma.apps.patient.models import CPatient
            data = row.get('value')
            docid = row.get('id')
            doc = row.get('doc')
            if not data or data is None:
                return row
            if not isinstance(data, dict) or not docid:
                return row
            else:
                if 'rev' in data:
                    data['_rev'] = data.pop('rev')
                case = cls.wrap(data)
                case.patient = None
                if doc == None:
                    # there's (I think) a bug in couchdb causing these to come back empty
                    try:
                        doc = CPatient.get_db().get(docid)
                    except Exception, e:
                        pass
                if doc and doc.get("doc_type") == "CPatient":
                    case.patient = CPatient.wrap(doc)
                return case
        return cls.view(view_name, 
                        include_docs=True,
                        wrapper=_patient_wrapper,
                        **params)
            
    

    @classmethod
    def view_with_patient(cls, view_name, **params):
        return cls.__view_with_patient(view_name, **params)
    
    @classmethod
    def get_with_patient(cls, view_name, id, **params):
        return cls.view_with_patient(view_name, key=id, **params).one()
                                     

    