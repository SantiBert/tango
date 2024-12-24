from django.db import models

# Create your models here.
class Subscription(models.Model):
    TRIAL = 'trial'
    BASIC = 'basic'
    PRO = 'pro'
    SUBSCRIPTION_CHOICES = (
        ( TRIAL, 'trial'),
        ( BASIC, 'basic'),
        ( PRO , 'pro')
    )
    startup = models.ForeignKey('startups.Startup', on_delete=models.PROTECT)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_status = models.CharField(max_length=100, choices=SUBSCRIPTION_CHOICES, default=TRIAL)
    stripe_trial_end_date = models.DateTimeField()
    
    def __str__(self):
        return self.startup.name