from django.db import models
from django.utils.crypto import get_random_string

class PrivateVisitorManager(models.Manager):
    def create(self, **kwargs):
        if 'unique_token' not in kwargs:
            kwargs['unique_token'] = get_random_string(length=100)
        return super().create(**kwargs)
