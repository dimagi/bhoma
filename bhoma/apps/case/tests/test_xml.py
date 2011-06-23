from django.test import TestCase
from bhoma.apps.patient import export as export
from django.test.client import Client
import os
from django.core.urlresolvers import reverse
from bhoma.apps.phone.xml import date_to_xml_string
from bhoma.apps.case.tests.util import check_xml_line_by_line
import xml

class XMLTest(TestCase):
    
    def testXMLEscaping(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "xml_test")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        # add the form that creates a case
        export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_general.xml"))
        
        # grab the case xml and check it against what we expect to get back
        c = Client()
        response = c.get(reverse("patient_case_xml", args=[patient.get_id]))
        # this call fails if it's not good xml
        et = xml.etree.ElementTree.fromstring(response.content)
        # for good measure
        self.assertTrue("&amp;" in response.content)
        self.assertTrue("&lt;" in response.content)
        