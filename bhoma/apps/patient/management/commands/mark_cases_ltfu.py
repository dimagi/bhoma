"""
This script loads random patients into the database.
"""

from django.core.management.base import LabelCommand
from datetime import datetime
from bhoma.apps.case.bhomacaselogic.ltfu import get_open_lost_cases,\
    close_as_lost

class Command(LabelCommand):
    help = "Searches the database for any cases that should be marked lost to follow up and closes them."
    
    def handle(self, *args, **options):
        asof = datetime.utcnow().date()
        cases = get_open_lost_cases(asof)
        for case in cases:
            assert(not case.closed and case.ltfu_date < asof)
            close_as_lost(case)
            case.patient.update_cases([case])
            case.patient.save()
