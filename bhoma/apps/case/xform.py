from bhoma.apps.case import const

"""
Work on cases based on XForms. In our world XForms are special couch documents.
"""
from bhoma.apps.case.models import CCase
from bhoma.utils import parsing
from bhoma.apps.case.models.couch import CCaseAction, CReferral
from bhoma.apps.patient.models import CPatient

def get_or_update_cases(xformdoc):
    """
    Given an xform document, update any case blocks found within it,
    returning a dicitonary mapping the case ids affected to the
    couch case document objects
    """
    case_blocks = extract_case_blocks(xformdoc)
    cases_touched = {}
    for case_block in case_blocks:
        case_doc = get_or_update_model(case_block)
        cases_touched[case_doc.case_id] = case_doc
    return cases_touched


def get_or_update_model(case_block):
    """
    Gets or updates an existing case, based on a block of data in a 
    submitted form.  Doesn't save anything.
    """
    if const.CASE_ACTION_CREATE in case_block:
        case_doc = CCase.from_doc(case_block)
        return case_doc
    else:
        case_id = case_block[const.CASE_TAG_ID]
        def patient_wrapper(row):
            """
            The wrapper bolts the patient object onto the case, if we find
            it, otherwise does what the view would have done in the first
            place and adds an empty patient property
            """
            
            data = row.get('value')
            docid = row.get('id')
            doc = row.get('doc')
            if not data or data is None:
                return row
            if not isinstance(data, dict) or not docid:
                return row
            else:
                data['_id'] = docid
                if 'rev' in data:
                    data['_rev'] = data.pop('rev')
                case = CCase.wrap(data)
                case.patient = None
                if doc and doc.get("doc_type") == "CPatient":
                    case.patient = CPatient.wrap(doc)
                return case
        
        case_doc = CCase.view("case/all_and_patient", 
                              key=case_id, 
                              include_docs=True,
                              wrapper=patient_wrapper).one()
        
        case_doc.update_from_block(case_block)
                        
        return case_doc
        
    
def extract_case_blocks(doc):
    """
    Extract all case blocks from a document, returning an array of dictionaries
    with the data in each case. 
    """
    if doc is None: return []  
    block_list = []
    try: 
        for key, value in doc.items():
            if const.CASE_TAG == key:
                # we explicitly don't support nested cases yet, so no need
                # to check further
                block_list.append(value) 
            else:
                # recursive call
                block_list.extend(extract_case_blocks(value))
    except AttributeError :
        # whoops, this wasn't a dictionary, an expected outcome in the recursive
        # case.  Fall back to base case
        return []
    
    return block_list