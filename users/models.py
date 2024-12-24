import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

from phonenumber_field.modelfields import PhoneNumberField

from pjbackend.utils import generate_verification_code
from .managers import PhoneNumberVerificationManager, CustomUserManager

from startups.models import Startup

max_length_name = settings.MAX_LENGTH_CONFIG['names']
max_length_tagline = settings.MAX_LENGTH_CONFIG['tag_line']
max_length_code = settings.MAX_LENGTH_CONFIG['verification_code']

class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=max_length_name, blank=True, null=True, unique = True, default = None)
    email = models.EmailField(unique= True)
    phone_number = PhoneNumberField()
    linkedin_url = models.URLField(blank=True)
    x_url = models.URLField(blank=True, null=True) 
    website_url = models.URLField(blank=True, null=True)
    calendly_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    picture_url = models.URLField(blank=True, null=True)
    tag_line = models.CharField(max_length = max_length_tagline, blank=True, null=True, default = None)
    is_temporary_pass = models.BooleanField(default=False)
    is_registered = models.BooleanField(default=False)
    is_terms_acepted = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["first_name","last_name", "password"]
    
    objects = CustomUserManager()
    
    def __str__(self):
        return self.email
    
    def get_startup(self):
        try:
            startup = Startup.objects.get(main_founder=self, is_active=True)
            return startup
        except Startup.DoesNotExist:
            pass
        try:
            startup = Startup.objects.get(founders__user=self, founders__is_confirmed=True, is_active=True)
            return startup
        except Startup.DoesNotExist:
            pass

        return None

class Experience(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    title = models.CharField(max_length=max_length_name, blank=True, null=True)
    company = models.CharField(max_length=max_length_name, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return f"User ->{self.user.email}, Experience-> {self.id}"
    
class PhoneNumberVerification(models.Model):
    phone_number = PhoneNumberField()
    verification_code = models.CharField(max_length=6)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    expiration_time = models.DateTimeField()

    objects = PhoneNumberVerificationManager()

    def generate_for_register(self, phone_number: str, user_id:str) -> None:
        """
        Generate a new verification code for signup method.
        """
        self.phone_number = phone_number
        self.user_id = user_id
        self.verification_code = generate_verification_code(
            max_length_code
        )
        expiration_seconds = settings.SIGNUP_EXPIRATION_SECONDS
        self.expiration_time = timezone.now() + timedelta(seconds=expiration_seconds)
        self.remove_old_codes(user_id)

    @classmethod
    def remove_old_codes(cls, user_id: str) -> None:
        cls.objects.filter(user_id=user_id).delete()

    @classmethod
    def verify(cls, user_id: str, verification_code: str) -> bool:
        """
        Check if the verification code is available for the time
        that is sended.
        Args:
            - user_id(str): user's user_id
            - verification_code(str): user's verification code
        Returns:
            - True if verification code is ok
            - False if not
        """
        try:
            now = timezone.now()
            phone_validation = cls.objects.get(
                user_id=user_id,
                verification_code=verification_code,
            )
            if phone_validation.expiration_time > now:
                return True
            else:
                return False
        except PhoneNumberVerification.DoesNotExist:
            return False