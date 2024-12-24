import pytest

from rest_framework.test import APIClient
from rest_framework import status

from django.urls import reverse

from users.models import CustomUser, PhoneNumberVerification, Experience

from .fixtures import (
    FAKE_USER_EMAIL,
    FAKE_USER_PASSWORD,
    FAKE_USER_PHONE_NUMBER,
    common_user,
    common_user_token)
from datetime import datetime
from django.utils import timezone

main_user = common_user
main_user_token = common_user_token


# ========================================================
# ======================= SIGN UP ========================
# ========================================================


@pytest.mark.django_db
def test_signup_successfully(mocker):
    client = APIClient()
    email = "john.smith2@example.com"
    data ={
        "email": email ,
        "password": "password123",
        "phoneNumber":"+543416207112",
        "isTermsAcepted":True
    }
    url = reverse("signup")
    mocker.patch("pjbackend.utils.send_sms", return_value=True)
    response = client.post(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("refreshToken", None) is not None
    result_user = CustomUser.objects.get(email=email)
    assert result_user.email == email
    


@pytest.mark.django_db
def test_signup_email_already_exists(main_user): 
    
    client = APIClient()
    data ={
        "email": FAKE_USER_EMAIL ,
        "password": "password123",
        "phoneNumber":FAKE_USER_PHONE_NUMBER,
        "isTermsAcepted":True,
    }
    url = reverse("signup")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"message": "Account already exists and is active"}



@pytest.mark.django_db
def test_signup_delete_account(mocker):
    client = APIClient()
    email = "john.smith2@example.com"
    
    data ={
        "email": email ,
        "password": "password123",
        "phoneNumber":"+543416207112",
        "isTermsAcepted": True
    }
    url = reverse("signup")
    mocker.patch("pjbackend.utils.send_sms", return_value=True)
    response = client.post(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("refreshToken", None) is not None
    result_user = CustomUser.objects.get(email=email)
    assert result_user.email == email
    # deactivate user
    user = CustomUser.objects.get(email=email)
    user.is_active = False
    user.is_registered = False
    user.save()

    data_2 = {
        "email": email ,
        "password": "password123",
        "phoneNumber":"+543416207112",
        "isTermsAcepted": True
    }

    response = client.post(url, data_2)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_signup_wrong_payload(mocker):
    client = APIClient()
    email = "2132412"
    data ={
        "email": email ,
        "password": "password123",
        "phoneNumber":"+543416207112",
        "isTermsAcepted": True
    }
    url = reverse("signup")
    mocker.patch("pjbackend.utils.send_sms", return_value=True)
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["message"] == "Bad request"

# ========================================================
# =================== VERIFICATE CODE =====================
# ========================================================

@pytest.mark.django_db
def test_signup_and_verification_code_successfully(mocker):
    client = APIClient()
    email = "john.smith2@example.com"
    signup_data ={
        "email": email ,
        "password": "password123",
        "phoneNumber":"+543416207112",
        "isTermsAcepted":True
    }
    signup_url = reverse("signup")
    mocker.patch("pjbackend.utils.send_sms", return_value=True)
    signup_response = client.post(signup_url, signup_data)
    assert signup_response.status_code == status.HTTP_200_OK
    token = signup_response.json().get('token') 
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    frist_query = CustomUser.objects.filter(email=email).first()
    assert frist_query.is_registered == False
    code = PhoneNumberVerification.objects.filter(user_id=frist_query.id).first()
    url = reverse("verificate-code")
    response = client.post(url, data={"code":code.verification_code})
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_signup_and_verification_code_wrong_code(mocker):
    client = APIClient()
    email = "john.smith2@example.com"
    signup_data ={
        "email": email ,
        "password": "password123",
        "phoneNumber":"+543416207112",
        "isTermsAcepted":True
    }
    signup_url = reverse("signup")
    mocker.patch("pjbackend.utils.send_sms", return_value=True)
    signup_response = client.post(signup_url, signup_data)
    assert signup_response.status_code == status.HTTP_200_OK
    token = signup_response.json().get('token') 
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    frist_query = CustomUser.objects.filter(email=email).first()
    assert frist_query.is_registered == False
    url = reverse("verificate-code")
    response = client.post(url, data={"code":"4545"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

# ========================================================
# ======================= LOGIN ==========================
# ========================================================


@pytest.mark.django_db
def test_login_successfully(main_user): 
    client = APIClient()
    data = {
        "email": FAKE_USER_EMAIL,
        "password": FAKE_USER_PASSWORD,
    }
    url = reverse("login")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("token", None) is not None
    assert response.json().get("refreshToken", None) is not None


@pytest.mark.django_db
def test_login_wrong_password(main_user):
    client = APIClient()
    data = {
        "email": FAKE_USER_EMAIL,
        "password": "WRONG_PASSWORD",
    }
    url = reverse("login")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json().get("token", None) is None


@pytest.mark.django_db
def test_login_wrong_payload(main_user): 
    client = APIClient()
    data = {
        "email": "Wornemail",
        "password": FAKE_USER_PASSWORD,
    }
    url = reverse("login")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("token", None) is None

# =====================================================
# ============= Edit Profile All Profile ==============
# =====================================================

@pytest.mark.django_db
def test_change_profile_successfully(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "firstName": "Jasmin",
        "lastName": "Daniel",
        "tagLine": "New Tagline",
        "linkedinUrl": "https://www.linkedin.com/in/new-link",
        "xUrl": "https://www.x.com/new-link",
        "websiteUrl": "https://www.newlink.com",
        "calendlyUrl": "https://calendly.com/other",
        "experiences": [
            {
             'title': 'New Experience',
             'company': 'New Company',
             'startDate': datetime(2020, 1, 1, tzinfo=timezone.utc),
             'endDate': datetime(2021, 1, 1, tzinfo=timezone.utc)
            },
            {
             'title': 'New Experience 2',
             'company': 'New Company 2',
             'startDate': datetime(2020, 2, 2, tzinfo=timezone.utc),
             'endDate': datetime(2021, 2, 2, tzinfo=timezone.utc)
            },
            ]
    }

    url = reverse("profile-update")
    response = client.put(url, data=payload,format='json')
    
    assert response.status_code == status.HTTP_200_OK
    user = CustomUser.objects.get(id=user.id)
    assert user.first_name == "Jasmin"
    assert user.last_name == "Daniel"
    assert user.tag_line == "New Tagline"
    assert user.linkedin_url =="https://www.linkedin.com/in/new-link"
    assert user.x_url == "https://www.x.com/new-link"
    assert user.website_url == "https://www.newlink.com"
    assert user.calendly_url == "https://calendly.com/other"
    experiencies = Experience.objects.filter(user=user)
    assert len(experiencies) == 2

@pytest.mark.django_db
def test_update_user_profile_invalid_data(main_user_token):
    token = main_user_token.get("token")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    payload = {
        'firstName': '',  
        'lastName': 'NewLastName',
        'tagLine': 'New Tag Line'
    }
    
    url = reverse("profile-update")
    response = client.put(url, data=payload,format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_update_user_profile_no_auth():
    client = APIClient()
    
    payload = {
        'firstName': 'NewFirstName',
        'lastName': 'NewLastName',
        'tagLine': 'New Tag Line'
    }
    url = reverse("profile-update")
    response = client.put(url, data=payload,format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# =====================================================
# ============= Edit Profile First Name ===============
# =====================================================


@pytest.mark.django_db
def test_change_profile_first_name_successfully(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "firstName": "Jane",
    }

    url = reverse("profile-first-name-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_200_OK
    user = CustomUser.objects.get(id=user.id)
    assert user.first_name == "Jane"


@pytest.mark.django_db
def test_change_profile_first_name_with_space_successfully(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    name = "Jane jr"
    payload = {
        "firstName": name,
    }

    url = reverse("profile-first-name-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_200_OK
    user = CustomUser.objects.get(id=user.id)
    assert user.first_name == name


@pytest.mark.django_db
def test_change_profile_first_name_numbers_and_symbols(main_user_token):
    token = main_user_token.get("token")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {"firstName": 9999}

    url = reverse("profile-first-name-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data.get("message") == "the first name cannot have numbers or symbols"

@pytest.mark.django_db
def test_change_profile_first_name_with_empy_payload(main_user_token):
    token = main_user_token.get("token")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    payload = {"firstName": ""}

    url = reverse("profile-first-name-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_change_profile_first_name_anonymous_user():
    client = APIClient()
    payload = {"firstName": "Jane"}
    url = reverse("profile-first-name-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =====================================================
# ============= Edit Profile Last Name ================
# =====================================================


@pytest.mark.django_db
def test_change_profile_last_name_successfully(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "lastName": "Dee",
    }

    url = reverse("profile-last-name-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_200_OK
    user = CustomUser.objects.get(id=user.id)
    assert user.last_name == "Dee"


@pytest.mark.django_db
def test_change_profile_last_name_with_spaces_successfully(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    name = "Dee John"
    payload = {"lastName": name}

    url = reverse("profile-last-name-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_200_OK
    user = CustomUser.objects.get(id=user.id)
    assert user.last_name == name


@pytest.mark.django_db
def test_change_profile_last_name_numbers_and_symbols(main_user_token):
    token = main_user_token.get("token")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {"lastName": "@+-*/"}

    url = reverse("profile-last-name-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data.get("message") == "the last name cannot have numbers or symbols"

@pytest.mark.django_db
def test_change_profile_last_name_with_empy_payload(main_user_token):
    token = main_user_token.get("token")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    payload = {"lastName": ""}

    url = reverse("profile-last-name-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_change_profile_last_name_anonymous_user():
    client = APIClient()
    payload = {"lastName": "Dee"}
    url = reverse("profile-last-name-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =====================================================
# ============= Edit Profile BIO ======================
# =====================================================


@pytest.mark.django_db
def test_change_profile_bio_successfully(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    test_bio = 'a test bio'
    
    payload = {
        "bio": test_bio
    }

    url = reverse("profile-bio-change")
    response = client.put(url, data=payload,format="json")
    assert response.status_code == status.HTTP_200_OK
    user = CustomUser.objects.get(id=user.id)
    assert user.bio == test_bio

@pytest.mark.django_db
def test_change_profile_bio_with_wrong_payload(main_user_token):
    token = main_user_token.get("token")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    payload = {"bio": None}

    url = reverse("profile-bio-change")
    response = client.put(url, data=payload,format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_change_profile_bio_anonymous_user():
    client = APIClient()
    test_bio = {
        "title": "Rich Text Example",
        "content": [
            {
            "type": "paragraph",
            "text": "This is a sample of rich text in JSON."
            },
            {
            "type": "image",
            "url": "https://example.com/image.jpg",
            "description": "An example image"
            },
            {
            "type": "link",
            "url": "https://example.com",
            "text": "Example link"
            }
            ]
        }
    
    payload = {"bio": test_bio}
    url = reverse("profile-bio-change")
    response = client.put(url, data=payload,format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# =====================================================
# ============= Edit Profile Social Media =============
# =====================================================

@pytest.mark.django_db
def test_update_social_media_profile_successfully(main_user_token):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    payload = {
        'linkedinUrl': 'https://www.newlinkedin.com/test',
        'xUrl': '', 
        'websiteUrl': '',
        'calendlyUrl': 'https://www.newcalendly.com/test',
    }

    url = reverse('profile-social-media-change')
    response = client.put(url, data =payload, format='json')

    assert response.status_code == status.HTTP_200_OK

    user = response.wsgi_request.user
    assert user.linkedin_url == payload['linkedinUrl']
    assert user.x_url == ''
    assert user.website_url == ''
    assert user.calendly_url == payload['calendlyUrl']
    

@pytest.mark.django_db
def test_update_social_media_profile_wrong_payload(main_user_token):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    payload = {
        'linkedinUrl': 'https://www.newlinkedin.com/test',
        'xUrl': 123, 
        'websiteUrl': '', 
        'calendlyUrl': 'https://www.newcalendly.com/test',
    }

    url = reverse('profile-social-media-change')
    response = client.put(url, data=payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_update_social_media_profile_anonymous_user():
    client = APIClient()

    payload = {
        'linkedinUrl': 'https://www.newlinkedin.com/test',
        'xUrl': '',
        'websiteUrl': '',
        'calendlyUrl': 'https://www.newcalendly.com/test',
    }
    url = reverse('profile-social-media-change')
    response = client.put(url, data=payload, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
#2 get and 4 post requests
# =====================================================
# ============= GETTING Profile AND FOR UPDATING  =====
# =====================================================

    
@pytest.mark.django_db
def test_profile_without_token():
    client = APIClient()
    url = reverse("profile")
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_get_profile_with_token(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    url = reverse("profile")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data.get("firstName") == user.first_name
    assert data.get("lastName") == user.last_name
    assert data.get("phoneNumber") == user.phone_number
    assert data.get("linkedinUrl") == user.linkedin_url
    assert data.get("xUrl") == user.x_url
    assert data.get("websiteUrl") == user.website_url
    assert data.get("calendlyUrl") == user.calendly_url
    assert data.get("bio") == user.bio
    assert data.get("pictureUrl") == user.picture_url
    assert data.get("professionalExperience") == []
    assert data.get("tagLine") == user.tag_line

@pytest.mark.django_db
def test_create_profile_with_empty_payload(main_user_token):
   token = main_user_token.get("token")
   client = APIClient()
   client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
   payload = {
        "firstName": "",
        "lastName": "",
        "tagLine": "",
}
   url = reverse("profile")
   response = client.post(url, data=payload)
   assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_profile_with_spaces_successfully(main_user_token):
   token = main_user_token.get("token")
   client = APIClient()
   client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
   payload = {
        "firstName": "Jane",
        "lastName": "Doe ",
        "tagLine" : "CEO of XYZ Company ",
    }
   url = reverse("profile")
   response = client.post(url, data=payload)
   assert response.status_code == status.HTTP_201_CREATED
   user_id = response.data['userId']
   user = CustomUser.objects.get(id=user_id)
   assert user.first_name == payload['firstName'].strip()
   assert user.last_name == payload['lastName'].strip()
   assert user.tag_line == payload['tagLine'].strip()


@pytest.mark.django_db
def test_change_profile_with_numbers_and_symbols(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    payload = {
        "firstName": "John123",
        "lastName": "Doe@+-*/",
        "tagLine": "CEO of XYZ Company"
    }

    url = reverse("profile")
    response = client.post(url, data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "firstName" in data["errors"]
    assert "lastName" in data["errors"]
    assert data["errors"]["firstName"][0] == "The first name cannot have numbers or symbols."
    assert data["errors"]["lastName"][0] == "The last name cannot have numbers or symbols."

@pytest.mark.django_db
def test_profile_update_without_token():
    client = APIClient()
    url = reverse("profile")
    response = client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_profile_create_with_token(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "firstName": "John",
        "lastName": "Doe",
        "tagLine": "CEO of XYZ Company"
    }
    url = reverse("profile")
    response = client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    user_result = CustomUser.objects.get(id=user.id)  
    assert user_result.first_name == payload['firstName']
    assert user_result.last_name == payload['lastName']
    assert user_result.tag_line == payload['tagLine']
    

@pytest.mark.django_db
def test_profile_create_with_invalid_token():
   client = APIClient()
   client.credentials(HTTP_AUTHORIZATION="Bearer " + "INVALID_TOKEN")
   url = reverse("profile")
   payload = {
        "firstName": "John",
        "lastName": "Doe",
        "tagLine": "CEO of XYZ Company"
   }
   response = client.post(url, data = payload, format='json') 
   assert response.status_code == status.HTTP_401_UNAUTHORIZED
   

# =====================================================
# ============= Edit Profile TagLine ==================
# =====================================================


@pytest.mark.django_db
def test_change_profile_tag_line_successfully(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "tagLine": "ETL Developer",
    }

    url = reverse("profile-tag-line-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_200_OK, "Failed to update tag line"
    user = CustomUser.objects.get(id=user.id)
    assert user.tag_line == "ETL Developer"


@pytest.mark.django_db
def test_change_profile_tag_line_with_spaces_successfully(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    tag_line = "Fizz Founder "
    payload = {"tagLine": tag_line}

    url = reverse("profile-tag-line-change")
    response = client.put(url, data=payload, format='json')
    assert response.status_code == status.HTTP_200_OK, "Failed to update tag line"
    user = CustomUser.objects.get(id=user.id)
    assert user.tag_line == tag_line.strip()


@pytest.mark.django_db
def test_change_profile_tag_line_numbers_and_symbols(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    tag_line = "FizzFounder@+-*/"
    payload = {"tagLine": tag_line}

    url = reverse("profile-tag-line-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_200_OK, "Failed to update tag line"
    user = CustomUser.objects.get(id=user.id)
    assert user.tag_line == tag_line


@pytest.mark.django_db
def test_change_profile_last_name_with_empty_payload(main_user_token):
    token = main_user_token.get("token")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    payload = {"tagLine": ""}

    url = reverse("profile-tag-line-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_change_profile_tag_line_anonymous_user():
    client = APIClient()
    payload = {"tagLine": "Anyonoymous User"}
    url = reverse("profile-tag-line-change")
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =====================================================
# ============= Creating Professional History =========
# =====================================================

    
@pytest.mark.django_db
def test_create_professional_history_successfully(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    start_date =  datetime(2023, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2023, 12, 31, tzinfo=timezone.utc)
    payload = {
        "listOfExperiences": [
            {
                "title": "Software Engineer",
                "company": "Tech Innovations",
                "startDate": start_date,
                "endDate": end_date,
            }
        ]
    }
    url = reverse("profile-professional-history")
    response = client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    experiences = user.experience_set.all()
    assert experiences.count() == len(payload["listOfExperiences"])

    experience = experiences.first()

    assert experience.title == payload['listOfExperiences'][0]['title'] 
    assert experience.company == payload['listOfExperiences'][0]['company']
    assert experience.start_date == payload['listOfExperiences'][0]['startDate']
    assert experience.end_date == payload['listOfExperiences'][0]['endDate']

@pytest.mark.django_db
def test_create_professional_history_with_end_date_none_successfully(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    start_date =  datetime(2023, 1, 1, tzinfo=timezone.utc)
    end_date = None
    payload = {
        "listOfExperiences": [
            {
                "title": "Software Engineer",
                "company": "Tech Innovations",
                "startDate": start_date,
                "endDate": end_date,
            }
        ]
    }
    url = reverse("profile-professional-history")
    response = client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    experiences = user.experience_set.all()
    assert experiences.count() == len(payload["listOfExperiences"])

    experience = experiences.first()

    assert experience.title == payload['listOfExperiences'][0]['title']
    assert experience.company == payload['listOfExperiences'][0]['company']
    assert experience.start_date == payload['listOfExperiences'][0]['startDate']
    assert experience.end_date == None

    
@pytest.mark.django_db
def test_create_professional_history_with_empty_payload(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    start_date =  datetime(2023, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2023, 12, 31, tzinfo=timezone.utc)
    payload = {
        "listOfExperiences": [
            {
                "title": "",
                "company": "",
                "startDate": start_date,
                "endDate": end_date,
            }
        ]
    }
    url = reverse("profile-professional-history")
    response = client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST 

@pytest.mark.django_db
def test_create_professional_history_with_invalid_token():
    client = APIClient()
    start_date =  datetime(2023, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2023, 12, 31, tzinfo=timezone.utc)
    payload = {
        "listOfExperiences": [
            {
                "title": "Software Engineer",
                "company": "Tech Innovations",
                "startDate": start_date,
                "endDate": end_date,
            }
        ]
    }
    url = reverse("profile-professional-history")
    response = client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_create_professional_history_with_invalid_dates(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    start_date =  datetime(2023, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
    payload = {
        "listOfExperiences": [
            {
                "title": "Software Engineer",
                "company": "Tech Innovations",
                "startDate": start_date,
                "endDate": end_date,
            }
        ]
    }
    url = reverse("profile-professional-history")
    response = client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_professional_history_with_no_token():
    client = APIClient()
    start_date =  datetime(2023, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2023, 12, 31, tzinfo=timezone.utc)
    payload = {
        "listOfExperiences": [
            {
                "title": "Software Engineer",
                "company": "Tech Innovations",
                "startDate": start_date,
                "endDate": end_date,
            }
        ]
    }
    url = reverse("profile-professional-history")
    response = client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_create_professional_history_with_future_start_date(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    start_date =  datetime(2029, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2029, 12, 31, tzinfo=timezone.utc)
    payload = {
        "listOfExperiences": [
            {
                "title": "Software Engineer",
                "company": "Tech Innovations",
                "startDate": start_date,
                "endDate": end_date,
            }
        ]
    }
    url = reverse("profile-professional-history")
    response = client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
@pytest.mark.django_db
def test_create_professional_history_with_wrong_format_dates(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    
    wrong_format_date = "January 1st, 2029"
    end_date = datetime(2023, 12, 31, tzinfo=timezone.utc)
    payload = {
        "listOfExperiences": [
            {
                "title": "Software Engineer",
                "company": "Tech Innovations",
                "startDate": wrong_format_date,
                "endDate": end_date,
            }
        ]
    }
     
    url = reverse("profile-professional-history")
    response = client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_multiple_professional_histories_successfully(main_user_token):
    token = main_user_token.get("token")
    user = main_user_token.get("user")    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    start_datep1 =  datetime(2021, 1, 1, tzinfo=timezone.utc)
    end_datep1 = datetime(2021, 12, 31, tzinfo=timezone.utc)
    start_datep2 =  datetime(2022, 1, 1, tzinfo=timezone.utc)
    end_datep2 = datetime(2022, 12, 31, tzinfo=timezone.utc)
    start_datep3 =  datetime(2023, 1, 1, tzinfo=timezone.utc)
    end_datep3 = datetime(2023, 12, 31, tzinfo=timezone.utc)

    payloads = {
        "listOfExperiences": [
            {
                "title": "Software Engineer",
                "company": "Tech Innovations",
                "startDate": start_datep1,
                "endDate": end_datep1,
            }, 
            {
                "title": "Software Engineer",
                "company": "Tech Innovations",
                "startDate": start_datep2,
                "endDate":end_datep2,
            },
            {
                "title": "Data Analyst",
                "company": "Data Science Labs",
                "startDate": start_datep3,
                "endDate": end_datep3,
            },
        ]
    }


    url = reverse("profile-professional-history")

    response = client.post(url, data=payloads, format='json')
    assert response.status_code == status.HTTP_201_CREATED

    experiences = user.experience_set.all().order_by('start_date')
    assert len(experiences) == len(payloads['listOfExperiences']) 
    
    for i, experience in enumerate(experiences):
        expected_experience = payloads['listOfExperiences'][i]
        assert experience.title == expected_experience['title']
        assert experience.company == expected_experience['company']
        assert experience.start_date == expected_experience['startDate']
        assert experience.end_date == expected_experience['endDate']

# =====================================================
# =================== Forgot Password =================
# =====================================================

@pytest.mark.django_db
def test_forgot_password_successfully(main_user_token):
    user = main_user_token.get("user")
    client = APIClient()
    
    payload = {'email':FAKE_USER_EMAIL}
    url = reverse('forgot-password')
    response = client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_200_OK
    new_query_user = CustomUser.objects.get(id=user.id)
    assert new_query_user.is_temporary_pass == True

@pytest.mark.django_db
def test_forgot_password_invalid_email(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {'email':"jane.max@example.com"}
    url = reverse('forgot-password')
    response = client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert 'User does not exist' in response.data['error']

# =====================================================
# =================== Change Password =================
# =====================================================

@pytest.mark.django_db
def test_change_password_successfully(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    new_password = 'newpassword123'
    url = reverse('change-password')
    
    data = {
        'oldPassword': FAKE_USER_PASSWORD, 
        'newPassword': new_password,
        'secondPassword':new_password
        }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    login_data = {
        "email": FAKE_USER_EMAIL,
        "password": new_password,
    }
    login_url = reverse("login")
    response_login = client.post(login_url, data=login_data)
    assert response_login.status_code == status.HTTP_200_OK
    assert response_login.json().get("token", None) is not None
    assert response_login.json().get("refreshToken", None) is not None


@pytest.mark.django_db
def test_reset_password_invalid_old_password(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    new_password = 'newpassword123'
    url = reverse('change-password')
    
    data = {
        'oldPassword': "Incorrect", 
        'newPassword': new_password,
        'secondPassword':new_password
        }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Incorrect Password' in response.data['error']

@pytest.mark.django_db
def test_reset_passwords_dontmatch(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    url = reverse('change-password')
    
    data = {
        'oldPassword': "Incorrect", 
        'newPassword': 'newpassword123',
        'secondPassword':'newpassword124'
        }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    errors = response.json().get('errors')
    assert errors['error'] == ["Passwords fields didn't match."]

# =====================================================
# =================== Resend SMS ======================
# =====================================================

@pytest.mark.django_db
def test_resend_sms_successfully(main_user_token, mocker):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {main_user_token.get('token')}")
    url = reverse('resend-code')
    send_sms_mock = mocker.patch("pjbackend.utils.send_sms", return_value=True)
    response = client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert send_sms_mock.called, "send_sms function was not called"
    assert send_sms_mock.call_count == 1, "send_sms function was not called once"

@pytest.mark.django_db
def test_resend_sms_invalid_token(main_user_token, mocker):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {'INVALID_TOKEN'}")
    url = reverse('resend-code')
    send_sms_mock = mocker.patch("pjbackend.utils.send_sms", return_value=True)
    response = client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not send_sms_mock.called, "send_sms function was called"

@pytest.mark.django_db
def test_resend_sms_anonymous_user(mocker):
    client = APIClient()
    url = reverse('resend-code')
    send_sms_mock = mocker.patch("pjbackend.utils.send_sms", return_value=True)
    response = client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not send_sms_mock.called, "send_sms function was called"
    
    
# =====================================================
# =================Delete Account =====================
# =====================================================

@pytest.mark.django_db
def test_reset_delete_account_successfully(main_user_token, mocker):
    token = main_user_token.get("token")
    user = main_user_token.get("user")
    user_id = user.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    url = reverse('delete-account')
    mocker.patch("pjbackend.utils.cancel_stripe_subscription", return_value=True)
    response = client.delete(url)
    assert response.status_code == status.HTTP_200_OK
    new_query = CustomUser.objects.get(id=user_id)
    assert new_query.phone_number == 'XXXXXXXXXXXXX'
    assert new_query.linkedin_url == ""
    assert new_query.first_name == ""
    assert new_query.last_name == ""
    assert new_query.is_registered is False

   
@pytest.mark.django_db
def test_delete_account_server_error(main_user_token, mocker):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    url = reverse('delete-account')

    # Simular que ocurre un error inesperado
    mocker.patch("users.models.Experience.objects.filter", side_effect=Exception("Unexpected error"))

    response = client.delete(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.data
    assert response.data["error"] == "Unexpected error"