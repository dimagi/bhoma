from django.conf import settings
from couchdbkit.ext.django.schema import *
from distutils.version import LooseVersion

"""Shared models"""


class AppVersionedDocument(Document):
    """Mixin to add a version attribute and properties to a document in couch."""
    
    app_version = StringProperty()
    # if the app version changes we have a record of the version that created it
    original_app_version = StringProperty() 
    
    def is_current(self):
        """
        Whether this patient is at the current app version
        """
        # no version, definitely not current
        if not self.app_version: return False
        return LooseVersion(self.app_version) == LooseVersion(settings.BHOMA_APP_VERSION)
        
    
    def requires_upgrade(self):
        """
        Whether this patient requires an upgrade, based on the app version number
        """
        # no version = upgrade fo sho
        if not self.app_version:  return True
        my_version = LooseVersion(self.app_version)
        settings_version = LooseVersion(settings.BHOMA_APP_VERSION)
        if len(my_version.version) >= 2 and len(settings_version.version) >= 2:
            return my_version.version[0] < settings_version.version[0] or \
                   my_version.version[1] < settings_version.version[1]
        else:
            return my_version < settings_version
                
    def save(self, *args, **kwargs):
        # override save to add the app version
        if not self.app_version:
            self.app_version = settings.BHOMA_APP_VERSION
        if not self.original_app_version:
            self.original_app_version = self.app_version
        super(AppVersionedDocument, self).save(*args, **kwargs)
    
    class Meta:
        app_label = 'patient'

        