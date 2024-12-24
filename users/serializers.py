import re
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from django.utils import timezone

from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .models import CustomUser, Experience

max_length_name = settings.MAX_LENGTH_CONFIG['names']
max_length_password = settings.MAX_LENGTH_CONFIG['password']
max_length_email = settings.MAX_LENGTH_CONFIG['email']
max_length_url = settings.MAX_LENGTH_CONFIG['url']
max_length_tag_line = settings.MAX_LENGTH_CONFIG['tag_line']
max_length_code = settings.MAX_LENGTH_CONFIG['verification_code']
max_length_description = settings.MAX_LENGTH_CONFIG['description']

class VerificateCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=max_length_code)

class SignUpSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=max_length_email)
    password = serializers.CharField(max_length=max_length_password)
    phoneNumber = PhoneNumberField()
    isTermsAcepted = serializers.BooleanField()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=max_length_email)
    password = serializers.CharField(max_length=max_length_password)
    
    default_error_messages = {
        "no_active_account": _("No active account found with the given credentials")
    }

class ProfileUpdateFirstNameSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=max_length_name)


class ProfileUpdateLastNameSerializer(serializers.Serializer):
    lastName = serializers.CharField(max_length=max_length_name)
    
class ProfileUpdateBioSerializer(serializers.Serializer):
    bio = serializers.CharField(max_length=max_length_description)
    
class ForgotPasswordSerlializer(serializers.Serializer):
    email = serializers.EmailField(max_length=max_length_email)

class RecoveryPasswordSerlializer(serializers.Serializer):
    email = serializers.EmailField(max_length=max_length_email)
    newPassword = serializers.CharField(max_length=max_length_password)

class ChangePasswordSerlializer(serializers.Serializer):
    oldPassword = serializers.CharField(max_length=max_length_password)
    newPassword = serializers.CharField(max_length=max_length_password)
    secondPassword = serializers.CharField(max_length=max_length_password)
    
    def validate(self, attrs):
        if attrs['newPassword'] != attrs['secondPassword']:
            raise serializers.ValidationError({"error": "Passwords fields didn't match."})
        return attrs
    
class ProfileUpdateSocialMediaSerializer(serializers.Serializer):
    linkedinUrl = serializers.URLField(max_length=max_length_url,required=False, allow_blank=True)
    xUrl = serializers.URLField(max_length=max_length_url,required=False, allow_blank=True)
    websiteUrl = serializers.URLField(max_length=max_length_url,required=False, allow_blank=True)
    calendlyUrl = serializers.URLField(max_length=max_length_url,required=False, allow_blank=True)

class ExperienceSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=max_length_name, required=True)
    company = serializers.CharField(max_length=max_length_name, required=True)
    startDate = serializers.DateTimeField(source='start_date')
    endDate = serializers.DateTimeField(source='end_date', allow_null=True)

    class Meta:
        model = Experience
        fields = ['title', 'company' ,'startDate', 'endDate']
    
    def validate_title_and_company(self, value):
        """Ensure that title and company are not empty."""
        if not value.get('title') or not value.get('company'): 
            raise serializers.ValidationError("Title and company cannot be empty.")
        return value

    def validate(self, attrs):
        """
        Check that the start date is before the end date.
        """
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date is None:
            raise serializers.ValidationError("Start date is required.")
        if start_date > timezone.now():
            raise serializers.ValidationError("Start date cannot be in the future.")
        # Check if end_date is provided since it's not required
        if end_date is not None and start_date >= end_date:
            raise serializers.ValidationError("End date must occur after start date.")

        return attrs 


class ExperienceSerializerV2(serializers.ModelSerializer):
    startDate = serializers.DateTimeField(source='start_date')
    endDate = serializers.DateTimeField(source='end_date', allow_null=True)

    class Meta:
        model = Experience
        fields = ['title', 'company' ,'startDate', 'endDate']

class ProfileSerializer(serializers.ModelSerializer):
    bio = serializers.CharField(required=False, allow_null=True)
    phoneNumber = PhoneNumberField(source='phone_number')  # Changed to camelCase
    professionalExperience = ExperienceSerializer(many=True, source='experience_set', read_only=True)  # Changed to camelCase
    firstName = serializers.CharField(source='first_name', max_length= settings.MAX_LENGTH_CONFIG['names'])
    lastName = serializers.CharField(source='last_name', max_length= settings.MAX_LENGTH_CONFIG['names'])
    tagLine = serializers.CharField(source='tag_line', max_length= settings.MAX_LENGTH_CONFIG['tag_line'])
    linkedinUrl = serializers.URLField(source='linkedin_url', allow_blank=True)
    xUrl = serializers.URLField(source='x_url', allow_blank=True)
    websiteUrl = serializers.URLField(source='website_url', allow_blank=True)
    pictureUrl = serializers.URLField(source='picture_url', allow_blank=True)
    calendlyUrl = serializers.URLField(source='calendly_url', allow_blank=True)
    experiences = serializers.SerializerMethodField(method_name="get_experiences")
    
    def get_experiences(self, obj):
        experiences = Experience.objects.filter(user_id=obj.id)
        serializers = ExperienceSerializerV2(experiences,many=True)
        return serializers.data
    
    class Meta:
        model = CustomUser
        fields = [
            'firstName', 
            'lastName',
            'email',
            'bio', 
            'phoneNumber', 
            'linkedinUrl', 
            'xUrl', 
            'websiteUrl', 
            'pictureUrl', 
            'calendlyUrl', 
            'professionalExperience', 
            'tagLine',
            'experiences'
            ] 

class CreateExperienceSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=max_length_name, required=True)
    company = serializers.CharField(max_length=max_length_name, required=True)
    startDate = serializers.DateTimeField(required=False, allow_null=True)
    endDate = serializers.DateTimeField(required=False, allow_null=True)

class UserProfileUpdateSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=max_length_name, required=False, allow_blank=True)
    lastName = serializers.CharField(max_length=max_length_name, required=False, allow_blank=True)
    tagLine = serializers.CharField(max_length=max_length_tag_line, required=False, allow_blank=True)
    bio = serializers.CharField(max_length=max_length_description, required=False, allow_blank=True)
    linkedinUrl = serializers.URLField(max_length=max_length_url, required=False, allow_blank=True)
    xUrl = serializers.URLField(max_length=max_length_url, required=False, allow_blank=True)
    websiteUrl = serializers.URLField(max_length=max_length_url, required=False, allow_blank=True)
    calendlyUrl = serializers.URLField(max_length=max_length_url, required=False, allow_blank=True)
    image = serializers.ImageField(required=False)
    experiences = CreateExperienceSerializer(many=True, required=False)
    
    def validate_firstName(self, value):
        if value.strip() == "":
            raise serializers.ValidationError("First Name cannot not be empty.")
        if not re.match(settings.REGEX_STRING, value.replace(" ", "")):
            raise serializers.ValidationError("The first name cannot have numbers or symbols.")
        return value

    def validate_lastName(self, value):
        if value.strip() == "":
            raise serializers.ValidationError("Last Name cannot not be empty.")
        if not re.match(settings.REGEX_STRING, value.replace(" ", "")):
            raise serializers.ValidationError("The last name cannot have numbers or symbols.")
        return value

class UserProfileCreateSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=max_length_name)
    lastName = serializers.CharField(max_length=max_length_name)
    tagLine = serializers.CharField(max_length=max_length_tag_line)
    bio = serializers.JSONField(required=False, allow_null=True)
    
    def validate_firstName(self, value):
        if value.strip() == "":
            raise serializers.ValidationError("First Name cannot not be empty.")
        if not re.match(settings.REGEX_STRING, value.replace(" ", "")):
            raise serializers.ValidationError("The first name cannot have numbers or symbols.")
        return value

    def validate_lastName(self, value):
        if value.strip() == "":
            raise serializers.ValidationError("Last Name cannot not be empty.")
        if not re.match(settings.REGEX_STRING, value.replace(" ", "")):
            raise serializers.ValidationError("The last name cannot have numbers or symbols.")
        return value

class ProfileUpdatetagLineSerializer(serializers.Serializer):
    tagLine = serializers.CharField(max_length = max_length_tag_line)

class ProfilePictureSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    
    def validate(self, data):
        image = data.get('image')
        if not image:
            raise serializers.ValidationError("Image field cannot be empty")
        return data

class SmallUserSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    pictureUrl = serializers.URLField(source='picture_url')
    
    class Meta:
        model = CustomUser
        fields = ['id','firstName', 'lastName', 'pictureUrl']