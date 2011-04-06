try:
    from bhoma.apps.xforms.tests.test_basic import *
    from bhoma.apps.xforms.tests.test_meta import *
    from bhoma.apps.xforms.tests.test_duplicates import *
    from bhoma.apps.xforms.tests.test_lock import *
except ImportError, e:
    # for some reason the test harness squashes these so log them here for clarity
    # otherwise debugging is a pain
    import logging
    logging.exception("bad test import!")
    raise
