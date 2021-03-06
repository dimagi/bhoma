from django.db.models import signals
from django.contrib.auth.models import Permission, Group
import logging

# map group/role name to permissions
BHOMA_PERMISSIONS = (("bhoma_view_pi_reports", "Can view clinic performance indicator reports."),
                     ("bhoma_enter_data", "Can view and enter patient data."),
                     ("bhoma_administer_clinic", "Can do clinic administration options."),
                     )

GROUPS = (("Clinic Support Worker", ("bhoma_enter_data",)),
          ("Clinic In-Charge", ("bhoma_enter_data", "bhoma_view_pi_reports",
                                "bhoma_administer_clinic")),
          ("District Manager", ("bhoma_enter_data", "bhoma_view_pi_reports",
                                "bhoma_administer_clinic")),
          )

def init_groups():
    """
    Initialize the default BHOMA groups (roles)
    """
    
    for group_name, perms in GROUPS:
        try:
            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions = [Permission.objects.get(codename=perm) for perm in perms]
            group.save()
        except Permission.DoesNotExist:
            logging.error(("Tried to load one of permissions: %s but it didn't exist! "
                           "Not all BHOMA groups have been created!  To fix this "
                           "problem run syncdb again and make sure you don't see "
                           "this error message") % ",".join(perms))