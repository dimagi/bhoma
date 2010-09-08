from django.dispatch import Signal
from bhoma.apps.xforms.signals import xform_saved

SENDER_CLINIC = "clinic"
SENDER_PHONE = "phone"

"""This signal is for when a form is added to a patient."""
# this is currently unused, so dropping.
# form_added_to_patient = Signal(providing_args=["patient_id", "form"])

"""
This signal is for _after_ a form is added to a patient and all the 
previous signals have been called.  This should only be used for 
dynmic data that nothing else should depend on (e.g. custom report 
fields).
"""
patient_updated = Signal(providing_args=["patient_id"])

def add_clinic_ids(sender, form, **kwargs):
    """
    Adds a top level clinic_ids prefix to a form.  This allows
    the form to sync with multiple clinics.
    """
    if not hasattr(form, "clinic_ids"):
        form.clinic_ids = []
    if "clinic_id" in form.meta and form.meta["clinic_id"] not in form.clinic_ids: 
        form.clinic_ids.append(form.meta["clinic_id"])
        form.save()

xform_saved.connect(add_clinic_ids)