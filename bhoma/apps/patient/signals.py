from django.dispatch import Signal
from bhoma.apps.xforms.signals import xform_saved

SENDER_CLINIC = "clinic"
SENDER_PHONE = "clinic"

"""This signal is for when a form is added to a patient."""
form_added_to_patient = Signal(providing_args=["patient", "form"])

"""
This signal is for _after_ a form is added to a patient and all the 
previous signals have been called.  This should only be used for 
dynmic data that nothing else should depend on (e.g. custom report 
fields).
"""
patient_updated = Signal(providing_args=["patient"])

