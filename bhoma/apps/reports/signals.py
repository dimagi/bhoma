from bhoma.apps.patient.signals import patient_updated

def update_pregnancies(sender, patient, **kwargs):
    """
    Update pregnancies of a patient.
    """
    from bhoma.apps.reports.calc.pregnancy import extract_pregnancies
    from bhoma.apps.reports.models import CPregnancy

    pregs = extract_pregnancies(patient)
    # manually remove old pregnancies, since all pregnancy data is dynamically generated
    for old_preg in CPregnancy.view("reports/pregnancies_for_patient", key=patient.get_id).all():
        old_preg.delete() 
    for preg in pregs:
        couch_pregnancy = preg.to_couch_object()
        couch_pregnancy.save()
    patient.save()

patient_updated.connect(update_pregnancies)