"""
Logic about phones and cases go here.
"""

def meets_sending_criteria(case, synclog):
    """
    Whether this case should be sent out.
    """
    # if never before synced, always include this
    if not synclog: return True
    # otherwise only sync something that's been modified since the date of the log
    return case.modified_on > synclog.date
    

