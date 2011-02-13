try:
    from bhoma.apps.patient.tests.test_import_export import *
    from bhoma.apps.patient.tests.test_replication import *
    from bhoma.apps.patient.tests.test_version_upgrade import *
except ImportError, e:
    # for some reason the test harness squashes these so log them here for clarity
    # otherwise debugging is a pain
    from dimagi.utils.logging import log_exception
    log_exception(e)
    raise
