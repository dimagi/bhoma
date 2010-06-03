
from couchdbkit.ext.django.forms import DocumentForm
from bhoma.apps.encounter.models import Encounter

class EncounterForm(DocumentForm):

    class Meta:
        document = Encounter
