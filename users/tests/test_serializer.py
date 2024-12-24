import pytest
from users.serializers import SignUpSerializer, LoginSerializer

from .fixtures import common_user, FAKE_USER_EMAIL, FAKE_USER_PASSWORD, FAKE_USER_PHONE_NUMBER

main_user = common_user

@pytest.mark.django_db
def test_sign_up_serializer(main_user):

    email = FAKE_USER_EMAIL
    password = FAKE_USER_PASSWORD
    phone_number = FAKE_USER_PHONE_NUMBER
    
    
    data = {
        "email": email,
        "password": password,
        "phoneNumber":phone_number,
        "isTermsAcepted": True
    }

    serializer = SignUpSerializer(data=data)
  
    assert serializer.is_valid() is True

@pytest.mark.django_db
def test_login_serializer_valid(main_user):

    email = FAKE_USER_EMAIL
    password = FAKE_USER_PASSWORD
    
    serializer = LoginSerializer(data={"email": email, "password": password})

    assert serializer.is_valid() is True
    
    credentials = serializer.validated_data
    assert "email" in credentials
    assert "password" in credentials
    assert credentials["email"] == email
    assert credentials["password"] == password
