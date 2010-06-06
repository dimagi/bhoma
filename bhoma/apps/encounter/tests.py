import os
from django.test import TestCase
from bhoma.apps.encounter.models import EncounterType
from bhoma.apps.xforms.models import XForm

class EncounterTest(TestCase):
    
    def testBasic(self):
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "xforms", "registration.xml")
        xform = XForm.from_file(file_path)
        encounter = EncounterType.objects.create(name="registration", xform=xform)
        