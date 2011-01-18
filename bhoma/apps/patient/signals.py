from django.dispatch import Signal
from bhoma.apps.xforms.signals import xform_saved, add_sha1

SENDER_CLINIC = "clinic"
SENDER_EXPORT = "export"
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
    if hasattr(form, "meta") and "clinic_id" in form.meta and form.meta["clinic_id"] not in form.clinic_ids: 
        form.clinic_ids.append(form.meta["clinic_id"])
        form.save()
xform_saved.connect(add_clinic_ids)

def fix_old_chw_ref_id(sender, form, **kwargs):
    chw_ref_id = form.chw_referral_id if hasattr(form, 'chw_referral_id') else None
    if chw_ref_id and len(chw_ref_id) == 7:
        form.chw_referral_id = '%s0%s' % (chw_ref_id[:4], chw_ref_id[4:])
        form.save()

xform_saved.connect(fix_old_chw_ref_id)

# wire this up too
xform_saved.connect(add_sha1)
