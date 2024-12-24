from django.db import models

from django.conf import settings

from startups.models import Startup, StartupCategory

max_length_name = settings.MAX_LENGTH_CONFIG['names']
max_length_email = settings.MAX_LENGTH_CONFIG['email']
max_length_description = settings.MAX_LENGTH_CONFIG['description']

class InvestmentRound(models.Model):
    startup = models.ForeignKey(Startup, on_delete=models.PROTECT)
    round_type =models.CharField(max_length=max_length_name)
    amount = models.IntegerField(blank=True, null=True)
    raised_amount = models.IntegerField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class InvestorUser(models.Model):
    VERIFIED = 'verified'
    NOT_VERIFIED = 'not_verified'
    PENDING = 'pending'
    verification_choices = [
        (VERIFIED, 'Verified'),
        (NOT_VERIFIED, 'Not Verified'),
        (PENDING, 'Pending')]
    round = models.ForeignKey(InvestmentRound, related_name="investors", on_delete=models.PROTECT)
    firm_name =  models.CharField(max_length=max_length_name)
    first_name = models.CharField(max_length=max_length_name)
    last_name = models.CharField(max_length=max_length_name)
    email = models.EmailField(max_length=max_length_email)
    amount_invested = models.IntegerField()
    invested_type =  models.CharField(max_length=max_length_description)
    is_verificated = models.CharField(max_length=max_length_name,choices = verification_choices, default=PENDING)
    is_active = models.BooleanField(default=True)

class InversorTemporal(models.Model):
    VERIFIED = 'verified'
    NOT_VERIFIED = 'not_verified'
    PENDING = 'pending'
    verification_choices = [
        (VERIFIED, 'Verified'),
        (NOT_VERIFIED, 'Not Verified'),
        (PENDING, 'Pending')]
    email = models.EmailField(max_length=max_length_email,unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    firm_name = models.CharField(max_length=255)
    website = models.URLField(max_length=255, blank=True, null=True)
    founding_year = models.CharField(max_length=20,blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    fund_stage = models.CharField(max_length=100, blank=True, null=True)
    fund_type = models.CharField(max_length=100, blank=True, null=True)
    linkedin_link = models.URLField(max_length=255, blank=True, null=True)
    twitter_link = models.URLField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    industry_categories = models.ManyToManyField(StartupCategory, blank=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=max_length_name,choices = verification_choices, default=PENDING)
    test = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"
    
class FavoriteInvestorsTemporal(models.Model):
    startup = models.ForeignKey(Startup, on_delete=models.PROTECT)
    investor = models.ForeignKey(InversorTemporal, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"{self.investor.first_name} {self.investor.last_name} - {self.startup.name}"