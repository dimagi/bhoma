from django.dispatch import Signal
from bhoma.apps.xforms.signals import xform_saved
from bhoma.apps.patient.processing import add_new_clinic_form

SENDER_CLINIC = "clinic"
SENDER_PHONE = "phone"

"""This signal is for when a form is added to a patient."""
form_added_to_patient = Signal(providing_args=["patient_id", "form"])

"""
This signal is for _after_ a form is added to a patient and all the 
previous signals have been called.  This should only be used for 
dynmic data that nothing else should depend on (e.g. custom report 
fields).
"""
patient_updated = Signal(providing_args=["patient_id"])

form_added_to_patient.connect(add_new_clinic_form, sender=SENDER_CLINIC)