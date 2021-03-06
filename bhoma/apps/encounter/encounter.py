from bhoma.apps.xforms.util import get_xform_by_namespace


class EncounterTypeRecord(object):
    """
    Base class for a record of an encounter type.  This is more of a 
    configuration class, as opposed to the django model which actually
    points at a specific form.
    """
    _name = None
    _type = None
    _namespace = None
    _legality_func = None
    _is_routine_visit = False
    
    def __init__(self, type, namespace, name=None, classification=None, 
                 is_routine_visit=False, legality_func=None):
        self._type = type
        self._namespace = namespace
        self._name = name if name is not None else type
        self._classification = classification
        self._is_routine_visit = is_routine_visit
        self._legality_func = legality_func
        
        
    @property
    def is_routine_visit(self):
        """
        Whether this is a routine visit (like a pregnancy checkup) or not.
        Default is False.
        """
        return self._is_routine_visit 
    
    @property
    def type(self):
        """Get the type associated with this"""
        if self._type == None: raise ValueError("No encounter type found!")
        return self._type
    
    @property
    def namespace(self):
        """Get the namespace associated with this"""
        if self._namespace == None: raise ValueError("No namespace found!")
        return self._namespace
    
    @property
    def name(self):
        """Get the type associated with this"""
        if self._name == None: return self.type
        return self._name
    
    @property
    def classification(self):
        """Get the classification (phone or clinic) associated with this"""
        return self._classification
    
    def is_active_for(self, patient):
        """
        Whether this type of encounter is available for a particular patient
        """
        legalfunc = self._legality_func
        if not legalfunc:
            legalfunc = lambda: True
        return not patient.is_deceased and legalfunc(patient)
    
    def get_xform(self):
        """
        Gets the xform associated with this type
        """
        return get_xform_by_namespace(self.namespace)
        
    