try:
    from bhoma.apps.phone.tests.test_custom_response import *
except ImportError, e:
    # for some reason the test harness squashes these so log them here for clarity
    # otherwise debugging is a pain
    import logging
    logging.exception("bad test import!")
    raise
