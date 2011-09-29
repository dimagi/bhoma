from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import json

class Command(BaseCommand):

    def handle(self, *args, **options):
        clinic_id = str(settings.BHOMA_CLINIC_ID)
        is_clinic = (len(clinic_id) > 4)

        server = settings.SSH_TUNNEL_SERVER
        user = 'clinic' if is_clinic else 'district'
        port = int('7%s%s' % (clinic_id[2], clinic_id[4:6] if is_clinic else '00'))

        print json.dumps({'server': server, 'user': user, 'port': port})
