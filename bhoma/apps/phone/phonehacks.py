from bhoma.apps.case.util import follow_type_from_form

"""
Hacks to get certain fields populating in the phone download
xml correctly in the absence of a real fix on the underlying
data
"""

def original_visit_type_transform(visit_type):
    VISIT_TYPE_MAPPING = {'under five': 'underfive',
                          'under_five': 'underfive',
                          'general visit': "general",
                          'general_visit': "general",
                          'delivery': 'delivery',
                          'sick pregnancy': 'sick_pregnancy',
                          'sick_pregnancy': 'sick_pregnancy',
                          'healthy pregnancy': "pregnancy",
                          'healthy_pregnancy': "pregnancy"
    }
    if visit_type in VISIT_TYPE_MAPPING:
        return VISIT_TYPE_MAPPING[visit_type]
    return visit_type

def followup_type_transform(visit_type):
    type = follow_type_from_form(visit_type)
    if type != "unknown": return type
    return visit_type
    