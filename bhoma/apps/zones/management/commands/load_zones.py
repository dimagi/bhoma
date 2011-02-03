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
        
class Command(LabelCommand):
    help = "Loads zones from the specified csv file."
    args = "<file_path>"
    label = 'valid file path'
    
    def handle(self, * args, ** options):
        if len(args) < 1:
            raise CommandError('Please specify %s.' % self.label)
        file_path = (args[0])
        load_clinic_zones(file_path, True)
                
    def __del__(self):
        pass
    

