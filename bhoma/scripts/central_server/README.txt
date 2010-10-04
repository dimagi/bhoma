============================================================================
     Scripts that should be linked and run on the central server
============================================================================

patient-upgrader.sh
-------------------

Checks the version of patients when they are updated (coming through sync 
or directly) and if it is less than the current BHOMA_APP_VERSION brings
them up to the latest version. 

patient-formslistener.sh
-------------------

Checks new forms coming in if they are meant to be linked to patients and
if they are not actually linked to the patient rebuilds the patient object.


conflict-resolver.sh
--------------------

Listens for all patient conflicts (when a patient is updated centrally by
a phone followup or upgrade and at the clinic) and resolves them by playing
back all of the form data.