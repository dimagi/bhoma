from bhoma.apps.djangoplus.fields import UUIDField
from django.db import models
import json
from django.contrib.contenttypes.models import ContentType

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
    django_type_key = "django_type"
    
    _id = UUIDField()
    
    def to_dict(self):
        # hat tip: http://stackoverflow.com/questions/757022/how-do-you-serialize-a-model-instance-in-django
        d = dict([(attr, getattr(self, attr)) for attr in \
                  [f.name for f in self._meta.fields]])
        
        ct = ContentType.objects.get_for_model(self)
        # include the model class as well
        d[self.django_type_key] = "%s.%s" % (ct.app_label, ct.model)
        return d
    
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