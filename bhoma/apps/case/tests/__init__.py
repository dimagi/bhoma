try:
    from bhoma.apps.case.tests.test_from_xform import *
    from bhoma.apps.case.tests.test_in_patient import *
    from bhoma.apps.case.tests.test_bhoma_flow import *
except ImportError, e:
    # for some reason the test harness squashes these so log them here for clarity
    # otherwise debugging is a pain
    from bhoma.utils.logging import log_exception
    log_exception(e)
    raise(e)
