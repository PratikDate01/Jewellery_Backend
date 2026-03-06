from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django_mongodb_backend.managers import MongoManager
import django_mongodb_backend.fields
from django.db import models

class ContentType(DjangoContentType):
    id = django_mongodb_backend.fields.ObjectIdAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    
    objects = MongoManager()

    class Meta:
        abstract = False
        db_table = 'django_content_type'
        verbose_name = 'content type'
        verbose_name_plural = 'content types'
        unique_together = [['app_label', 'model']]
