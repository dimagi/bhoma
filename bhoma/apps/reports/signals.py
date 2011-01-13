from bhoma.apps.patient.signals import patient_updated
import logging

def update_pregnancy_report_data(sender, patient_id, **kwargs):
    """
    Update pregnancies of a patient.
    """
    from bhoma.apps.reports.calc.pregnancy import PregnancyReportData
    from bhoma.apps.reports.models import PregnancyReportRecord
    from bhoma.apps.patient.models import CPatient
    
    patient = CPatient.get(patient_id)
    # manually remove old pregnancies, since all pregnancy data is dynamically generated
    for old_preg in PregnancyReportRecord.view("reports/pregnancies_for_patient", key=patient_id).all():
        old_preg.delete() 
    for preg in patient.pregnancies:
        preg_report_data = PregnancyReportData(patient, preg)
        couch_pregnancy = preg_report_data.to_couch_object()
        couch_pregnancy.save()
    patient.save()

patient_updated.connect(update_pregnancy_report_data)