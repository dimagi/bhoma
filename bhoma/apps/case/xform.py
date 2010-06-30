from bhoma.apps.case import const

"""
Work on cases based on XForms. In our world XForms are special couch documents.
"""
from bhoma.apps.case.models import CCase

def update_cases(xformdoc):
    """
    Given an xform document, update any case blocks found within it,
    returning a dicitonary mapping the case ids affected to the
    couch case document objects
    """
    case_blocks = extract_case_blocks(xformdoc)
    cases_touched = {}
    for case_block in case_blocks:
        case_doc = create_or_update(case_block)
        cases_touched[case_doc.case_id] = case_doc
    return cases_touched


def create_or_update(case_block):
    """Create or update a case based on a block of data in a submitted form"""
    if const.CASE_ACTION_CREATE in case_block:
        case_doc = CCase.from_doc(case_block)
        case_doc.save()
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
    
    if block_list:
        print "found case blocks: %s" % block_list 
    return block_list