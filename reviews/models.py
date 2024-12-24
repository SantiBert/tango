from django.db import models
from django.conf import settings
from startups.models import Startup

max_length_email = settings.MAX_LENGTH_CONFIG['email']

class Review(models.Model):
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE)
    email = models.EmailField(max_length=max_length_email, blank=False)
    overal_rating = models.IntegerField()
    team_value = models.IntegerField(blank=True, null=True)
    problem_value = models.IntegerField(blank=True, null=True)
    solution_value = models.IntegerField(blank=True, null=True)
    gtmstrategy_value = models.IntegerField(blank=True, null=True)
    marketopp_value = models.IntegerField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
