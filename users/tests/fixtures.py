import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

FAKE_USER_LAST_NAME = "Doe"
FAKE_USER_FIRST_NAME = "Jane"
FAKE_USER_USERNAME = "JDoe"
FAKE_USER_EMAIL = "jane.doe@example.com"
FAKE_USER_PHONE_NUMBER = "+543416207111"
FAKE_USER_LINKEDIN_URL = "https://www.linkedin.com/in/janedoe"
FAKE_USER_X_URL = "https://www.x.com/janedoe"
FAKE_USER_WEBSITE_URL = "https://www.janedoe.com"
FAKE_USER_CALENDLY_URL = "https://calendly.com/janedoe"
FAKE_USER_PASSWORD = "newuser789"

FAKE_STARTUP_MAIN_FOUNDER_EMAIL = "john.smith@example.com"
FAKE_STARTUP_MAIN_FOUNDER_FIRST_NAME = "Smith"
FAKE_STARTUP_MAIN_FOUNDER_LAST_NAME = "John"
FAKE_STARTUP_MAIN_FOUNDER_USERNAME = 'JSmith'
FAKE_STARTUP_MAIN_FOUNDER_PHONE_NUMBER = "+15555555554"

@pytest.mark.django_db
@pytest.fixture
def common_user():
    user_model = get_user_model()
    user, created = user_model.objects.get_or_create(
        phone_number=FAKE_USER_PHONE_NUMBER,
        first_name=FAKE_USER_FIRST_NAME,
        last_name=FAKE_USER_LAST_NAME,
        email=FAKE_USER_EMAIL,
        username=FAKE_USER_USERNAME,
        linkedin_url=FAKE_USER_LINKEDIN_URL,
        x_url=FAKE_USER_X_URL,
        website_url=FAKE_USER_WEBSITE_URL,
        calendly_url=FAKE_USER_CALENDLY_URL,
        is_registered = True
    )
    user.set_password(FAKE_USER_PASSWORD)
    user.save()
    return user

@pytest.mark.django_db
@pytest.fixture
def common_user_token():
    """Returns a dict with the next structure
    {
        "token": user_token,
        "user": Custom user object,
        "refresh_token": refresh_token,
    }
    """
    client = APIClient()
    url = reverse("login")
    User = get_user_model()
    user, created = User.objects.get_or_create(
        phone_number=FAKE_USER_PHONE_NUMBER,
        first_name=FAKE_USER_FIRST_NAME,
        last_name=FAKE_USER_LAST_NAME,
        email=FAKE_USER_EMAIL,
        username=FAKE_USER_USERNAME,
        linkedin_url=FAKE_USER_LINKEDIN_URL,
        x_url=FAKE_USER_X_URL,
        website_url=FAKE_USER_WEBSITE_URL,
        calendly_url=FAKE_USER_CALENDLY_URL,
        is_registered = True
    )
    
    user.set_password(FAKE_USER_PASSWORD)
    user.save()

    
    secondary_user, created = User.objects.get_or_create(
        first_name=FAKE_STARTUP_MAIN_FOUNDER_FIRST_NAME,
        last_name=FAKE_STARTUP_MAIN_FOUNDER_LAST_NAME,
        email=FAKE_STARTUP_MAIN_FOUNDER_EMAIL,
        phone_number=FAKE_STARTUP_MAIN_FOUNDER_PHONE_NUMBER,
        username=FAKE_STARTUP_MAIN_FOUNDER_USERNAME,
        linkedin_url=FAKE_USER_LINKEDIN_URL,
        x_url=FAKE_USER_X_URL,
        website_url=FAKE_USER_WEBSITE_URL,
        calendly_url=FAKE_USER_CALENDLY_URL,
        is_registered = True)
    secondary_user.set_password(FAKE_USER_PASSWORD)
    secondary_user.save()
    
    payload = {
        "email": FAKE_USER_EMAIL,
        "password": FAKE_USER_PASSWORD,
    }
    response = client.post(url, payload)
    
    secondary_payload = {
        "email": FAKE_STARTUP_MAIN_FOUNDER_EMAIL,
        "password": FAKE_USER_PASSWORD,
    }
    secondary_response = client.post(url, secondary_payload)
    
    return {
        "token": response.data.get("token"),
        "user": user,
        "refresh_token": response.data.get("refresh_token"),
        "secondary_user":secondary_user,
        "secondary_token": secondary_response.data.get("token"),
    }

@pytest.mark.django_db
@pytest.fixture
def common_user_founder():
    User = get_user_model()
    user, created = User.objects.get_or_create(
        first_name=FAKE_STARTUP_MAIN_FOUNDER_FIRST_NAME,
        last_name=FAKE_STARTUP_MAIN_FOUNDER_LAST_NAME,
        email=FAKE_STARTUP_MAIN_FOUNDER_EMAIL,
        phone_number=FAKE_STARTUP_MAIN_FOUNDER_PHONE_NUMBER,
        username=FAKE_STARTUP_MAIN_FOUNDER_USERNAME,
        linkedin_url=FAKE_USER_LINKEDIN_URL,
        x_url=FAKE_USER_X_URL,
        website_url=FAKE_USER_WEBSITE_URL,
        calendly_url=FAKE_USER_CALENDLY_URL,
        is_registered = True)
    user.set_password(FAKE_USER_PASSWORD)
    user.save()
    return user