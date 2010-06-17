from bhoma.apps.djangoplus.fields import UUIDField
from django.db import models
import json
from django.contrib.contenttypes.models import ContentType
from bhoma.apps.djangocouch.utils import DEFAULT_DJANGO_TYPE_KEY, model_to_dict

class CouchModel(models.Model):
    """
    A model to attach a uid to things for couchdb support.
    This currently only works with first order objects, won't 
    do anything special with foreign keys or relationships besides 
    just save the keys themselves.
    
    It arbitrarily stores the model name in the "django_type" field.
    This can be overridden by the subclass in django_type_key
    
    This model can be used with the couch_post_save signal to 
    automatically save all model data redundantly in couchdb.
    """
    django_type_key = DEFAULT_DJANGO_TYPE_KEY
    
    _id = UUIDField()
    
    def to_dict(self, fields=None, exclude=None):
        return model_to_dict(self, django_type_key=self.django_type_key)
        
    
    def to_json(self):
        return json.dumps(self.to_dict())
    
    
    class Meta:
        abstract = True

class DemoModel(CouchModel):
    
    name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.name

# load our signals.
import bhoma.apps.djangocouch.signals 