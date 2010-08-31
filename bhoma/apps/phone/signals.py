from bhoma.apps.phone.processing import add_new_phone_form
from bhoma.apps.patient.signals import SENDER_PHONE, form_added_to_patient

form_added_to_patient.connect(add_new_phone_form, sender=SENDER_PHONE)