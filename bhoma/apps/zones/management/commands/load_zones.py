"""
This script imports locations from a csv file into the database.
The csv file should have columns in the order:
Province, District, Facility_Name, Code, Facility Type, Latitude, Longitude
"""

import os
import random
from django.core.management.base import CommandError
from django.core.management.base import LabelCommand
from bhoma.apps.zones.loader import load_clinic_zones
from optparse import make_option
        
class Command(LabelCommand):
    help = "Loads zones from the specified csv file."
    args = "<file_path>"
    label = 'valid file path'
    option_list = LabelCommand.option_list + \
        (make_option('--purge', action='store_true', dest='purge', default=False,
            help='Tells the app to purge existing clinic zone information before running.'),)

    
    def handle(self, * args, ** options):
        if len(args) < 1:
            raise CommandError('Please specify %s.' % self.label)
        file_path = (args[0])
        load_clinic_zones(file_path, options["purge"], True)
                
    def __del__(self):
        pass
    

