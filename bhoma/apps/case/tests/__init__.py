try:
    from bhoma.apps.case.tests.test_adult_visit import *
    from bhoma.apps.case.tests.test_chw_referrals import *
    from bhoma.apps.case.tests.test_clinic_cases import *
    from bhoma.apps.case.tests.test_death import *
    from bhoma.apps.case.tests.test_from_xform import *
    from bhoma.apps.case.tests.test_in_patient import *
    from bhoma.apps.case.tests.test_ltfu import *
    from bhoma.apps.case.tests.test_phone_followups import *
    from bhoma.apps.case.tests.test_pregnancy import *
    from bhoma.apps.case.tests.test_xml import *
except ImportError, e:
    # for some reason the test harness squashes these so log them here for clarity
    # otherwise debugging is a pain
    import logging
    logging.exception("bad test import!")
    raise
