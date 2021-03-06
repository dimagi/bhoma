try:
    from bhoma.apps.patient.tests.test_bugs import *
    from bhoma.apps.patient.tests.test_import_export import *
    from bhoma.apps.patient.tests.test_replication import *
    from bhoma.apps.patient.tests.test_version_upgrade import *
    from bhoma.apps.patient.tests.test_utils import *
except ImportError, e:
    # for some reason the test harness squashes these so log them here for clarity
    # otherwise debugging is a pain
    import logging
    logging.exception("bad test import!")
    raise
