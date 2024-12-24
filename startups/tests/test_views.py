import datetime
import logging
import pytest
import stripe
import uuid
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import MagicMock,patch

from pjbackend.constants import INDUSTRIES_CATEGORIES, INDUSTRIES_SUBCATEGORIES

from django.urls import reverse

from users.tests.fixtures import (
    common_user_token, 
    common_user_founder
    )
from .fixtures import (
    common_startup, 
    common_secondary_startup,
    common_third_startup,
    FAKE_STARTUP_DATA
    )
from startups.models import (
    StartupCategory,
    StartupSubcategory,
    StartupTechSector,
    Startup,
    StartupVideo,
    StartupImage,
    StartupLocation,
    StartupSlidedeck,
    StartupBusinessTraction,
    StartupTopCustomer,
    StartupShare,
    Founder,
    PrivateVisitor,
    PublicVisitor
)

from users.models import CustomUser
from payment.models import Subscription

main_user_token = common_user_token
second_user = common_user_founder

main_startup = common_startup
second_startup = common_secondary_startup
third_startup =  common_third_startup

TEST_STARTUP_DATA = {
    "startup_name":"EcoGreen Solutions",
    "startup_description":"An environmentally friendly startup focused on renewable energy and sustainability.",
    "startup_location": "Bessemer, Alabama, United States",
    "startup_industry":"Clean Energy",
    "startup_stage" :  Startup.SEED,
    "startup_foundation_date": datetime.date.today(),
    "startup_site_web": "https://www.ecogreensolutions.com",
    "startup_new_name": "Tech Innovations Inc.",
    "startup_new_description":'A cutting-edge technology startup specializing in artificial intelligence solutions.',
    "startup_new_location" : "Hoover, Alabama, United States",
    "startup_new_industry": "Information Technology",
    "startup_new_stage": Startup.PRE_SEED,
    "startup_new_site_web": "https://www.techinnovations.com",
    "startup_new_video_url": "https://www.youtube.com/watch?v=123456",
}

TEST_NEW_FOUNDER_DATA = {
    "email":"user@founder.com",
    "first_name": "Clark",
    "last_name": "Kent",
    "role":"Friend"
}

FAKE_UUID = 'a8098c1a-f86e-11da-bd1a-00112444be1e'

logger = logging.getLogger(__name__)
@pytest.fixture
def mock_upload_file_to_s3():
    def upload_file_to_s3(file):
        return 'https://examplebucket.s3.amazonaws.com/media/public/test_pitch_deck.pdf'
    def upload_video_to_s3(file):
        return 'https://examplebucket.s3.amazonaws.com/media/public/test_video.mp4'
    def upload_image_to_s3(file):
        return 'https://examplebucket.s3.amazonaws.com/media/public/test_image.jpg'

    mock = MagicMock(side_effect=upload_file_to_s3)
    mock.upload_video_to_s3 = MagicMock(side_effect=upload_video_to_s3)
    mock.upload_image_to_s3 = MagicMock(side_effect=upload_image_to_s3)
    return mock

@pytest.fixture
def mock_startup_category():
    category = StartupCategory.objects.create(
        name = INDUSTRIES_CATEGORIES[0].get("name"),
        code = INDUSTRIES_CATEGORIES[0].get("code")
    )
    subcategories = INDUSTRIES_SUBCATEGORIES.get(category.code)
    subcategory = StartupSubcategory.objects.create(
        name = subcategories[0].get("name"),
        code = subcategories[0].get("code"),
        category = category 
    )
    
    return subcategory

@pytest.fixture
def mock_startup_category_second():
    category = StartupCategory.objects.create(
        name = INDUSTRIES_CATEGORIES[1].get("name"),
        code = INDUSTRIES_CATEGORIES[1].get("code")
    )
    subcategories = INDUSTRIES_SUBCATEGORIES.get(category.code)
    subcategory = StartupSubcategory.objects.create(
        name = subcategories[0].get("name"),
        code = subcategories[0].get("code"),
        category = category 
    )
    
    return subcategory

@pytest.fixture
def mock_startup_tech_sector():
    tech_sector = StartupTechSector.objects.create(
        name = INDUSTRIES_CATEGORIES[0].get("name")
    )
    return tech_sector

@pytest.fixture
def mock_startup_tech_sector_second():
    tech_sector = StartupTechSector.objects.create(
        name = INDUSTRIES_CATEGORIES[1].get("name")
    )
    return tech_sector


# ========================================================
# =================== GET STARTUP ========================
# ========================================================

@pytest.mark.django_db
def test_get_startup_successfully(main_user_token,main_startup):
    token = main_user_token.get("token")
    founder = main_user_token.get("secondary_user")
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    url = reverse("startup")
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()

    assert uuid.UUID(data.get("id")) == main_startup.id
    assert data.get("name") == main_startup.name
    assert data.get("description") == main_startup.description
    assert data.get("industry").get("name") == main_startup.industry_category.name
    assert data.get("websiteUrl") == main_startup.website_url
    assert data.get("stage") == Startup.SEED
    assert data.get("employeeCount") == main_startup.employee_count
    assert data.get("isAbleToShare") == True
    
    video_url = StartupVideo.objects.filter(startup=main_startup, is_active = True)[0].url
    image_url = StartupImage.objects.filter(startup=main_startup,is_active = True)[0].url
    location = StartupLocation.objects.filter(startup=main_startup)[0].full_name
    
    assert data.get("videoUrl") == video_url
    assert data.get("imageUrl") == image_url
    assert data.get("location") == location
    
    business_traction = StartupBusinessTraction.objects.filter(startup_id=main_startup.id)
    
    business_traction_result = data.get("businessTractions")
    assert business_traction_result.get("businessModel") == [business_traction[0].business_model]
    assert business_traction_result.get("businessRevenueSources") == business_traction[0].business_revenue_sources
    assert business_traction_result.get("mrr") == business_traction[0].mrr
    
   
    top_customers = StartupTopCustomer.objects.filter(business_traction=business_traction[0])
    assert len(business_traction_result.get("topCustomers")) == top_customers.count()
    
    assert business_traction_result.get("topCustomers")[0].get("name") == top_customers[0].name
    assert business_traction_result.get("topCustomers")[0].get("url") == top_customers[0].url
    
    founders = Founder.objects.filter(startup_id=main_startup.id)
    
    assert len(data.get("founders")) == founders.count()
    assert data.get("founders")[1].get("firstName") == founder.first_name
    assert data.get("founders")[1].get("lastName") == founder.last_name
    
 
@pytest.mark.django_db
def test_get_not_startup(main_user_token,main_startup,second_user):
    token = main_user_token.get("token")

    startup = Startup.objects.get(id=main_startup.id)
    Founder.objects.get(user_id=main_startup.main_founder.id, startup_id=main_startup.id).delete()
    new_user = CustomUser.objects.get(id=second_user.id)
    startup.main_founder = new_user
    startup.save()
    
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    url = reverse("startup")
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_get_startup_anonymous_user():
    client = APIClient()
    
    url = reverse("startup")
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ========================================================
# ================ CREATE STARTUP ========================
# ========================================================

@pytest.mark.django_db
def test_create_startup_success(main_user_token, mock_startup_category, mock_startup_tech_sector):
    token = main_user_token.get("token")
    industry_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":TEST_STARTUP_DATA["startup_location"],
        "industry":industry_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)

    assert response.status_code == status.HTTP_201_CREATED
    assert 'startupId' in response.data
    
    startup_id = response.data['startupId']
    
    #Delete stripe register
    # Obtener los IDs de Stripe para cancelar la suscripción
    subscription = Subscription.objects.get(startup_id=startup_id)
    stripe_subscription_id = subscription.stripe_subscription_id
    stripe_customer_id = subscription.stripe_customer_id

    # Cancelar la suscripción de Stripe
    if stripe_subscription_id:
        stripe.Subscription.delete(stripe_subscription_id)

    # Eliminar el cliente de Stripe
    if stripe_customer_id:
        stripe.Customer.delete(stripe_customer_id)


@pytest.mark.django_db
def test_create_startup_duplicate(
    main_user_token,
    main_startup, 
    mock_startup_category_second,
    mock_startup_tech_sector):
    token = main_user_token.get("token")
    industry_id = mock_startup_category_second.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":TEST_STARTUP_DATA["startup_location"],
        "industry":industry_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("error") == "You already have a Startup created, you cannot have more than one"
    

@pytest.mark.django_db
def test_create_startup_with_alternative_data(
    main_user_token, 
    mock_startup_category,
    mock_startup_tech_sector):
    token = main_user_token.get("token")
    categoty_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":TEST_STARTUP_DATA["startup_location"],
        "industry":categoty_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":"",
        "websiteUrl":"",
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert 'startupId' in response.data
    
    startup_id = response.data['startupId']
    
    #Delete stripe register
    # Obtener los IDs de Stripe para cancelar la suscripción
    subscription = Subscription.objects.get(startup_id=startup_id)
    stripe_subscription_id = subscription.stripe_subscription_id
    stripe_customer_id = subscription.stripe_customer_id

    # Cancelar la suscripción de Stripe
    if stripe_subscription_id:
        stripe.Subscription.delete(stripe_subscription_id)

    # Eliminar el cliente de Stripe
    if stripe_customer_id:
        stripe.Customer.delete(stripe_customer_id)

@pytest.mark.django_db
def test_create_startup_invalid_blank_name(main_user_token, mock_startup_category,mock_startup_tech_sector):
    token = main_user_token.get("token")
    categoty_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    data = {
        "name": "",
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":TEST_STARTUP_DATA["startup_location"],
        "industry":categoty_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }
    
    url = reverse("startup")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_startup_invalid_name(main_user_token, mock_startup_category,mock_startup_tech_sector):
    token = main_user_token.get("token")
    categoty_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    long_name ="A" * 151
    data = {
        "name": long_name,
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":TEST_STARTUP_DATA["startup_location"],
        "industry": categoty_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_startup_invalid_description(main_user_token,mock_startup_category, mock_startup_tech_sector):
    token = main_user_token.get("token")
    categoty_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    long_description ="A" * 1001
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":long_description,
        "location":TEST_STARTUP_DATA["startup_location"],
        "industry": categoty_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_startup_invalid_location(main_user_token,mock_startup_category, mock_startup_tech_sector):
    token = main_user_token.get("token")
    categoty_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    long_location ="A" * 151
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":long_location,
        "industry": categoty_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_startup_blank_location(main_user_token,mock_startup_category, mock_startup_tech_sector):
    token = main_user_token.get("token")
    categoty_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":"",
        "industry":categoty_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_startup_invalid_industry(main_user_token, mock_startup_category, mock_startup_tech_sector):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    categoty_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    long_industry ="A" * 151
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":long_industry,
        "techSector":tech_sector_id,
        "industry": categoty_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_startup_blank_industry(main_user_token, mock_startup_category):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    categoty_id = mock_startup_category.id
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":"",
        "industry": categoty_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_startup_invalid_employee_count(main_user_token, mock_startup_category, mock_startup_tech_sector):
    token = main_user_token.get("token")
    industry_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":TEST_STARTUP_DATA["startup_location"],
        "industry":industry_id,
        "techSector":tech_sector_id,
        "employeeCount": 99,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_startup_blank_employee_count(
    main_user_token, 
    mock_startup_category,
    mock_startup_tech_sector):
    token = main_user_token.get("token")
    industry_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":TEST_STARTUP_DATA["startup_location"],
        "industry": industry_id,
        "techSector":tech_sector_id,
        "employeeCount": "",
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_startup_invalid_web_site(main_user_token, mock_startup_category, mock_startup_tech_sector):
    token = main_user_token.get("token")
    industry_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    long_web_site ="A" * 501
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":TEST_STARTUP_DATA["startup_location"],
        "industry": industry_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":long_web_site,
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_startup_invalid_foundation_date(main_user_token, mock_startup_category, mock_startup_tech_sector):
    token = main_user_token.get("token")
    industry_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":TEST_STARTUP_DATA["startup_location"],
        "industry":industry_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":5555
    }

    url = reverse("startup")
    response = client.post(url, data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_startup_anonymous_user(mock_startup_category, mock_startup_tech_sector):
    industry_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector.id
    client = APIClient()
    data = {
        "name":TEST_STARTUP_DATA["startup_name"],
        "description":TEST_STARTUP_DATA["startup_description"],
        "location":TEST_STARTUP_DATA["startup_location"],
        "industry": industry_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.ONE_TO_TEN,
        "stage":TEST_STARTUP_DATA["startup_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_site_web"],
        "foundationDate":TEST_STARTUP_DATA["startup_foundation_date"]
    }

    url = reverse("startup")
    response = client.post(url, data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ========================================================
# ================== EDIT STARTUP ========================
# ========================================================

@pytest.mark.django_db
def test_edit_startup_success(main_user_token, main_startup, mock_startup_category_second, mock_startup_tech_sector_second):
    token = main_user_token.get("token")
    industry_id = mock_startup_category_second.id
    tech_sector_id = mock_startup_tech_sector_second.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    payload = {
        "name":TEST_STARTUP_DATA["startup_new_name"],
        "description":TEST_STARTUP_DATA["startup_new_description"],
        "location":TEST_STARTUP_DATA["startup_new_location"],
        "industry": industry_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.TEN_TO_FIFTY,
        "stage":TEST_STARTUP_DATA["startup_new_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_new_site_web"]
    }

    url = reverse("startup-edit",kwargs={"startupId": main_startup.id})
    response = client.put(url, data=payload)
    
    assert response.status_code == status.HTTP_200_OK
    assert 'startupId' in response.data
    
    new_query = Startup.objects.get(id=main_startup.id,is_active=True)
    assert new_query.name == TEST_STARTUP_DATA["startup_new_name"]
    assert new_query.description == TEST_STARTUP_DATA["startup_new_description"]
    assert new_query.industry_category.name == mock_startup_category_second.name
    assert new_query.employee_count == Startup.TEN_TO_FIFTY
    assert new_query.stage == TEST_STARTUP_DATA["startup_new_stage"]
    assert new_query.website_url == TEST_STARTUP_DATA["startup_new_site_web"]
    
    location = StartupLocation.objects.filter(startup=main_startup)[0].full_name
    
    assert location == TEST_STARTUP_DATA["startup_new_location"]

@pytest.mark.django_db
def test_edit_startup_wrong_id(main_user_token, mock_startup_category_second, mock_startup_tech_sector_second):
    industry_id = mock_startup_category_second.id
    tech_sector_id = mock_startup_tech_sector_second.id
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    payload = {
        "name":TEST_STARTUP_DATA["startup_new_name"],
        "description":TEST_STARTUP_DATA["startup_new_description"],
        "location":TEST_STARTUP_DATA["startup_new_location"],
        "industry": industry_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.TEN_TO_FIFTY,
        "stage":TEST_STARTUP_DATA["startup_new_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_new_site_web"]
    }

    url = reverse("startup-edit",kwargs={"startupId": FAKE_UUID})
    response = client.put(url, data=payload)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_startup_not_authorized(
    main_user_token, 
    second_startup, 
    mock_startup_category,
    mock_startup_tech_sector_second):
    industry_id = mock_startup_category.id
    tech_sector_id = mock_startup_tech_sector_second.id

    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    Founder.objects.filter(startup=0).delete()
    
    payload = {
        "name":TEST_STARTUP_DATA["startup_new_name"],
        "description":TEST_STARTUP_DATA["startup_new_description"],
        "location":TEST_STARTUP_DATA["startup_new_location"],
        "industry": industry_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.TEN_TO_FIFTY,
        "stage":TEST_STARTUP_DATA["startup_new_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_new_site_web"]
    }

    url = reverse("startup-edit",kwargs={"startupId": second_startup.id})
    response = client.put(url, data=payload)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    

@pytest.mark.django_db
def test_edit_startup_anonymous_user(main_startup, mock_startup_category_second, mock_startup_tech_sector_second):
    industry_id = mock_startup_category_second.id
    tech_sector_id = mock_startup_tech_sector_second.id
    client = APIClient()
    
    payload = {
        "name":TEST_STARTUP_DATA["startup_new_name"],
        "description":TEST_STARTUP_DATA["startup_new_description"],
        "location":TEST_STARTUP_DATA["startup_new_location"],
        "industry": industry_id,
        "techSector":tech_sector_id,
        "employeeCount": Startup.TEN_TO_FIFTY,
        "stage":TEST_STARTUP_DATA["startup_new_stage"],
        "websiteUrl":TEST_STARTUP_DATA["startup_new_site_web"]
    }

    url = reverse("startup-edit",kwargs={"startupId": main_startup.id})
    response = client.put(url, data=payload)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ========================================================
# =============== EDIT STARTUP LOCATION ==================
# ========================================================

@pytest.mark.django_db
def test_edit_startup_location_success(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    payload = {
        "location":TEST_STARTUP_DATA["startup_new_location"]
    }

    url = reverse("startup-edit-location", kwargs={"startupId": main_startup.id})
    response = client.put(url, data=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == "Location updated successfully"

    location = StartupLocation.objects.filter(startup=main_startup)[0].full_name
    assert location == TEST_STARTUP_DATA["startup_new_location"]

@pytest.mark.django_db
def test_edit_startup_location_cofunder_success(main_user_token, third_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    payload = {
        "location":TEST_STARTUP_DATA["startup_new_location"]
    }

    url = reverse("startup-edit-location", kwargs={"startupId": third_startup.id})
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_200_OK
    
@pytest.mark.django_db  
def test_edit_startup_location_wrong_id(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")  # Ensure correct header format

    payload = {
        "location": TEST_STARTUP_DATA["startup_new_location"]
    }
    url = reverse("startup-edit-location", kwargs={"startupId": FAKE_UUID})
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db  
def test_edit_startup_location_not_authorized(main_user_token,second_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    payload = {
        "location": TEST_STARTUP_DATA["startup_new_location"]
    }
    url = reverse("startup-edit-location", kwargs={"startupId": second_startup.id})
    response = client.put(url, data=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_startup_location_anonymous_user(main_startup):
    client = APIClient()

    payload = {
        "location": TEST_STARTUP_DATA["startup_new_location"]
    }
    url = reverse("startup-edit-location", kwargs={"startupId": main_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ========================================================
# =============== EDIT STARTUP NAME ======================
# ========================================================

@pytest.mark.django_db
def test_edit_startup_name_success(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "name":TEST_STARTUP_DATA["startup_new_name"]
    }
    url = reverse("startup-edit-name", kwargs={"startupId": main_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code ==status.HTTP_200_OK
    new_query = Startup.objects.get(id= main_startup.id, is_active=True )
    assert new_query.name == TEST_STARTUP_DATA["startup_new_name"]

@pytest.mark.django_db
def test_cofunder_edit_startup_name_success(main_user_token, third_startup  ):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "name":TEST_STARTUP_DATA["startup_new_name"]
    }
    url = reverse("startup-edit-name", kwargs={"startupId": third_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code ==status.HTTP_200_OK
    new_query = Startup.objects.get(id=third_startup.id, is_active=True )
    assert new_query.name == TEST_STARTUP_DATA["startup_new_name"]
    
@pytest.mark.django_db
def test_edit_startup_name_wrong_id(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "name":TEST_STARTUP_DATA["startup_new_name"]
    }
    url = reverse("startup-edit-name", kwargs={"startupId": FAKE_UUID})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_startup_name_not_authorized(main_user_token,second_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    payload = {
        "name":TEST_STARTUP_DATA["startup_new_name"]
    }
    url = reverse("startup-edit-name", kwargs={"startupId": second_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_startup_name_anonymous_user(main_startup):
    client = APIClient()
    payload = {
        "name":TEST_STARTUP_DATA["startup_new_name"]
    }
    url = reverse("startup-edit-name", kwargs={"startupId": main_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ========================================================
# =============== EDIT STARTUP STAGE ==================
# ========================================================

@pytest.mark.django_db
def test_edit_startup_stage_success(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "stage":TEST_STARTUP_DATA["startup_new_stage"]
    }
    url = reverse("startup-edit-stage", kwargs={"startupId": main_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_200_OK
    new_query = Startup.objects.get(id= main_startup.id, is_active=True)
    assert new_query.stage == TEST_STARTUP_DATA["startup_new_stage"]
    
@pytest.mark.django_db
def test_cofunder_edit_startup_stage_success(main_user_token, third_startup ):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "stage":TEST_STARTUP_DATA["startup_new_stage"]
    }
    url = reverse("startup-edit-stage", kwargs={"startupId":third_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_200_OK
    new_query = Startup.objects.get(id=third_startup.id, is_active=True)
    assert new_query.stage == TEST_STARTUP_DATA["startup_new_stage"]

@pytest.mark.django_db
def test_edit_startup_stage_with_wrong_id(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "stage":TEST_STARTUP_DATA["startup_new_stage"]
    }
    url = reverse("startup-edit-stage", kwargs={"startupId": FAKE_UUID})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_startup_stage_not_authorized(main_user_token,second_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "stage":TEST_STARTUP_DATA["startup_new_stage"]
    }
    url = reverse("startup-edit-stage", kwargs={"startupId": second_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    

@pytest.mark.django_db
def test_edit_startup_stage_anonymous_user(main_startup):
    client = APIClient()
    payload = {
        "stage":TEST_STARTUP_DATA["startup_new_stage"]
    }
    url = reverse("startup-edit-stage", kwargs={"startupId": main_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ========================================================
# =============== EDIT STARTUP INDUSTRY ==================
# ========================================================

@pytest.mark.django_db
def test_edit_startup_industry_success(main_user_token, main_startup, mock_startup_category_second):
    token = main_user_token.get("token")
    industry_id = mock_startup_category_second.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "industry":industry_id
    }
    url = reverse("startup-edit-industry", kwargs={"startupId": main_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_200_OK
    new_query = Startup.objects.get(id= main_startup.id, is_active=True)
    assert new_query.industry_category_id == mock_startup_category_second.id
    assert new_query.industry_category.name == mock_startup_category_second.name

@pytest.mark.django_db
def test_cofunder_edit_startup_industry_success(main_user_token, third_startup, mock_startup_category_second):
    token = main_user_token.get("token")
    industry_id = mock_startup_category_second.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "industry":industry_id
    }
    url = reverse("startup-edit-industry", kwargs={"startupId": third_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_200_OK
    new_query = Startup.objects.get(id=third_startup.id, is_active=True)
    assert new_query.industry_category_id == mock_startup_category_second.id
    assert new_query.industry_category.name == mock_startup_category_second.name

@pytest.mark.django_db
def test_edit_startup_industry_with_wrong_id(main_user_token, mock_startup_category_second):
    token = main_user_token.get("token")
    industry_id = mock_startup_category_second.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "industry":industry_id
    }
    url = reverse("startup-edit-industry", kwargs={"startupId": FAKE_UUID})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND   

@pytest.mark.django_db
def test_edit_startup_industry_not_authorized(main_user_token, second_startup, mock_startup_category):
    token = main_user_token.get("token")
    industry_id = mock_startup_category.id
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "industry":industry_id
    }
    url = reverse("startup-edit-industry", kwargs={"startupId": second_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND  

@pytest.mark.django_db
def test_edit_startup_industry_anonymous_user(main_startup, mock_startup_category_second):
    client = APIClient()
    industry_id = mock_startup_category_second.id
    payload = {
        "industry":industry_id
    }
    url = reverse("startup-edit-industry", kwargs={"startupId": main_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
# ========================================================
# ===================== Founders =========================
# ========================================================

@pytest.mark.django_db
def test_get_founders_list_success(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("founders", kwargs={"startupId": main_startup.id})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3

@pytest.mark.django_db
def test_founders_get_list_as_a_cofunder_success(main_user_token, third_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("founders", kwargs={"startupId": third_startup.id})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3

@pytest.mark.django_db
def test_get_founders_wrong_starup_id(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("founders", kwargs={"startupId": FAKE_UUID})
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_get_founders_not_authorized(main_user_token, second_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("founders", kwargs={"startupId": second_startup.id})
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_get_founders_list_anonymous_user(main_startup):
    client = APIClient()
    
    url = reverse("founders", kwargs={"startupId": main_startup.id})
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_create_founders_success(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    data = [
        {"firstName": "John", "lastName": "Doe", "email": "john@example.com", "role":"master"},
        {"firstName": "Janise", "lastName": "Doe", "email": "jane@example.com", "role":"sub-boss"}
    ]
    url = reverse("founders", kwargs={"startupId": main_startup.id})
    
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED

    assert Founder.objects.filter(startup=main_startup, first_name="John").exists()
    assert Founder.objects.filter(startup=main_startup, first_name="Janise").exists()

@pytest.mark.django_db
def test_create_founders_duplicate_email(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    Founder.objects.create(startup=main_startup, first_name="Janise", last_name="Doe")

    data = [
        {"firstName": "John", "lastName": "Doe", "email": "test@example.com"},
        {"firstName": "Janise", "lastName": "Doe", "email": "jane@example.com"}
    ]
    
    url = reverse("founders", kwargs={"startupId": main_startup.id})
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED

    assert Founder.objects.filter(startup=main_startup).count() == 5
    
@pytest.mark.django_db
def test_create_founders_wrong_payload(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    data = {"firstName": "John", "lastName": "Doe", "email": "john@example.com"}
    url = reverse("founders", kwargs={"startupId": main_startup.id})
    
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_founders_wrong_starup_id(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    data = [
        {"firstName": "John", "lastName": "Doe", "email": "john@example.com"},
        {"firstName": "Janise", "lastName": "Doe", "email": "jane@example.com"}
    ]
    
    url = reverse("founders", kwargs={"startupId": FAKE_UUID})
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
@pytest.mark.django_db
def test_create_founders_anonymous_user(main_startup):
    client = APIClient()
    data = {"firstName": "John", "lastName": "Doe", "email": "john@example.com"}
    
    url = reverse("founders", kwargs={"startupId": main_startup.id})
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
# ========================================================
# ================ Confirm Founder =======================
# ========================================================

@pytest.mark.django_db
def test_confirm_founders_success(main_startup):
    client = APIClient()
    
    founder = Founder.objects.create(
        startup=main_startup,
        first_name = TEST_NEW_FOUNDER_DATA["first_name"], 
        last_name = TEST_NEW_FOUNDER_DATA["last_name"], 
        email = TEST_NEW_FOUNDER_DATA["email"], 
        role = TEST_NEW_FOUNDER_DATA["role"]
    )
    data = {"confirm":True}
    url = reverse("founder-confirm", kwargs={"startupId": main_startup.id,"founderId":founder.id})
    response = client.post(url, data)
    assert response.status_code == status.HTTP_200_OK
   
    
@pytest.mark.django_db
def test_confirm_founders_wrong_startup_id(main_startup):
    client = APIClient()
    
    founder = Founder.objects.create(
        startup=main_startup,
        first_name = TEST_NEW_FOUNDER_DATA["first_name"], 
        last_name = TEST_NEW_FOUNDER_DATA["last_name"], 
        email = TEST_NEW_FOUNDER_DATA["email"], 
        role = TEST_NEW_FOUNDER_DATA["role"]
    )
    data = {"confirm":True}
    url = reverse("founder-confirm", kwargs={"startupId": FAKE_UUID,"founderId":founder.id})
    response = client.post(url, data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    
@pytest.mark.django_db
def test_confirm_founders_wrong_founder_id(main_startup):
    client = APIClient()
    
    Founder.objects.create(
        startup=main_startup,
        first_name = TEST_NEW_FOUNDER_DATA["first_name"], 
        last_name = TEST_NEW_FOUNDER_DATA["last_name"], 
        email = TEST_NEW_FOUNDER_DATA["email"], 
        role = TEST_NEW_FOUNDER_DATA["role"]
    )
    data = {"confirm":True}
    url = reverse("founder-confirm", kwargs={"startupId": main_startup.id,"founderId":999})
    response = client.post(url, data)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_confirm_founders_wrong_payload(main_startup):
    client = APIClient()
    
    founder = Founder.objects.create(
        startup=main_startup,
        first_name = TEST_NEW_FOUNDER_DATA["first_name"], 
        last_name = TEST_NEW_FOUNDER_DATA["last_name"], 
        email = TEST_NEW_FOUNDER_DATA["email"], 
        role = TEST_NEW_FOUNDER_DATA["role"]
    )
    url = reverse("founder-confirm", kwargs={"startupId": main_startup.id,"founderId":founder.id})
    response = client.post(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

# ========================================================
# ================== Edit Founder ========================
# ========================================================

@pytest.mark.django_db
def test_edit_founder_successfully(mocker,main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    founder = Founder.objects.filter(startup=main_startup).first()
    
    payload = {
        "firstName": TEST_NEW_FOUNDER_DATA["first_name"], 
        "lastName": TEST_NEW_FOUNDER_DATA["last_name"], 
        "email": TEST_NEW_FOUNDER_DATA["email"], 
        "role":TEST_NEW_FOUNDER_DATA["role"]
    }
    
    url = reverse("founder-edit", kwargs={"startupId": main_startup.id, "founderId":founder.id})
    mocker.patch("pjbackend.utils.send_email", return_value=True)
    response = client.put(url,data=payload, format='json')
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_edit_founder_wrong_startup_id(mocker,main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    founder = Founder.objects.filter(startup=main_startup).first()
    payload = {
        "firstName": TEST_NEW_FOUNDER_DATA["first_name"], 
        "lastName": TEST_NEW_FOUNDER_DATA["last_name"], 
        "email": TEST_NEW_FOUNDER_DATA["email"], 
        "role":TEST_NEW_FOUNDER_DATA["role"]
    }
    
    url = reverse("founder-edit", kwargs={"startupId": FAKE_UUID, "founderId":founder.id})
    mocker.patch("pjbackend.utils.send_email", return_value=True)
    response = client.put(url,data=payload, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_founder_wrong_founder_id(mocker,main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "firstName": TEST_NEW_FOUNDER_DATA["first_name"], 
        "lastName": TEST_NEW_FOUNDER_DATA["last_name"], 
        "email": TEST_NEW_FOUNDER_DATA["email"], 
        "role":TEST_NEW_FOUNDER_DATA["role"]
    }
    url = reverse("founder-edit", kwargs={"startupId": main_startup.id, "founderId":999})
    mocker.patch("pjbackend.utils.send_email", return_value=True)
    response = client.put(url,data=payload, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_edit_founder_anonymous_user(mocker,main_startup):
    client = APIClient()
    founder = Founder.objects.filter(startup=main_startup).first()
    payload = {
        "firstName": TEST_NEW_FOUNDER_DATA["first_name"], 
        "lastName": TEST_NEW_FOUNDER_DATA["last_name"], 
        "email": TEST_NEW_FOUNDER_DATA["email"], 
        "role":TEST_NEW_FOUNDER_DATA["role"]
    }
    url = reverse("founder-delete", kwargs={"startupId": main_startup.id, "founderId":founder.id})
    mocker.patch("pjbackend.utils.send_email", return_value=True)
    response = client.put(url,data=payload, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ========================================================
# ================== Delete Founder ======================
# ========================================================

@pytest.mark.django_db
def test_delete_founder_successfully(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    founder = Founder.objects.filter(startup=main_startup)[1]
    
    url = reverse("founder-delete", kwargs={"startupId": main_startup.id, "founderId":founder.id})
    response = client.delete(url)
    assert response.status_code == status.HTTP_200_OK
    
@pytest.mark.django_db
def test_delete_founder_wrong_startup_id(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    founder = Founder.objects.filter(startup=main_startup).first()
    
    url = reverse("founder-delete", kwargs={"startupId": FAKE_UUID, "founderId":founder.id})
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_delete_founder_wrong_founder_id(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("founder-delete", kwargs={"startupId": main_startup.id, "founderId":999})
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_founder_anonymous_user(main_startup):
    client = APIClient()
    
    founder = Founder.objects.filter(startup=main_startup).first()
    
    url = reverse("founder-delete", kwargs={"startupId": main_startup.id, "founderId":founder.id})
    response = client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
# ========================================================
# ===================== StartupEditWebsite ===============
# ======================================================== 

@pytest.mark.django_db
def test_edit_startup_website_successfully(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")  # Ensure correct header format

    payload = {
        "websiteUrl":TEST_STARTUP_DATA["startup_new_site_web"]
    }
    url = reverse("startup-edit-website", kwargs={"startupId": main_startup.id})
    response = client.put(url, data = payload)
    print(response)
    assert response.status_code == status.HTTP_200_OK
    new_query = Startup.objects.get(id= main_startup.id, is_active=True)
    assert new_query.website_url == TEST_STARTUP_DATA["startup_new_site_web"]

@pytest.mark.django_db
def test_cofunder_edit_startup_website_successfully(main_user_token, third_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")  # Ensure correct header format

    payload = {
        "websiteUrl":TEST_STARTUP_DATA["startup_new_site_web"]
    }
    url = reverse("startup-edit-website", kwargs={"startupId": third_startup.id})
    response = client.put(url, data = payload)
    print(response)
    assert response.status_code == status.HTTP_200_OK
    new_query = Startup.objects.get(id=third_startup.id, is_active=True)
    assert new_query.website_url == TEST_STARTUP_DATA["startup_new_site_web"]

@pytest.mark.django_db
def test_edit_startup_website_wrong_id(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "websiteUrl":TEST_STARTUP_DATA["startup_new_site_web"]
    }
    url = reverse("startup-edit-website", kwargs={"startupId": FAKE_UUID})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND 

@pytest.mark.django_db
def test_edit_startup_website_anonymous_user(main_startup):
    client = APIClient()
    payload = {
        "websiteUrl":TEST_STARTUP_DATA["startup_new_site_web"]
    }
    url = reverse("startup-edit-website", kwargs={"startupId": main_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ========================================================
# ===================== StartupEditVideo ===============
# ========================================================    

@pytest.mark.django_db
def test_edit_startup_video_successfully(main_user_token, main_startup, mock_upload_file_to_s3):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    video_file = SimpleUploadedFile("test_video.mp4", b"file_content", content_type="video/mp4")
    payload = {"video": video_file}

    url = reverse("startup-edit-video", kwargs={"startupId": main_startup.id})

    with patch('startups.views.utils.upload_file_to_s3', mock_upload_file_to_s3.upload_video_to_s3):
        response = client.put(url, data=payload, format='multipart')
    
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response data: {response.json()}")
   
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data.get("message") == "Startup Video updated successfully"

   
    new_video = StartupVideo.objects.filter(startup=main_startup,is_active = True)
    assert new_video[0].url == "https://examplebucket.s3.amazonaws.com/media/public/test_video.mp4"


@pytest.mark.django_db
def test_cofunder_edit_startup_video_successfully(main_user_token, third_startup, mock_upload_file_to_s3):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    video_file = SimpleUploadedFile("test_video.mp4", b"file_content", content_type="video/mp4")
    payload = {"video": video_file}

    url = reverse("startup-edit-video", kwargs={"startupId": third_startup.id})

    with patch('startups.views.utils.upload_file_to_s3', mock_upload_file_to_s3.upload_video_to_s3):
        response = client.put(url, data=payload, format='multipart')
    
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response data: {response.json()}")
   
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data.get("message") == "Startup Video updated successfully"

   
    new_video = StartupVideo.objects.filter(startup=third_startup,is_active = True)
    assert new_video[0].url == "https://examplebucket.s3.amazonaws.com/media/public/test_video.mp4"

@pytest.mark.django_db
def test_edit_startup_video_wrong_id(main_user_token, mock_upload_file_to_s3):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    video_file = SimpleUploadedFile("test_video.mp4", b"file_content", content_type="video/mp4")
    
    payload = {
        "video": video_file
    }
    
    url = reverse("startup-edit-video", kwargs={"startupId": FAKE_UUID})
    with patch('startups.views.utils.upload_file_to_s3', mock_upload_file_to_s3.upload_video_to_s3):
        response = client.put(url, data=payload, format='multipart')
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_startup_video_anonymous_user(main_startup, mock_upload_file_to_s3):
    client = APIClient()
    video_file = SimpleUploadedFile("test_video.mp4", b"file_content", content_type="video/mp4")
    payload = {
        "video":video_file
    }
    url = reverse("startup-edit-video", kwargs={"startupId": main_startup.id})
    with patch('startups.views.utils.upload_file_to_s3', mock_upload_file_to_s3.upload_video_to_s3):
        response = client.put(url, data = payload, format='multipart')
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ========================================================
# ================= Delete Startup Video =================
# ========================================================

@pytest.mark.django_db
def test_delete_startup_video_successfully(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    url = reverse("startup-edit-video", kwargs={"startupId": main_startup.id})

    response = client.delete(url)
   
    assert response.status_code == status.HTTP_200_OK
    
    assert StartupVideo.objects.filter(startup_id=main_startup.id, is_active=True).exists() == False


@pytest.mark.django_db
def test_delete_startup_video_wrong_id(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    url = reverse("startup-edit-video", kwargs={"startupId": FAKE_UUID})

    response = client.delete(url)
   
    assert response.status_code == status.HTTP_404_NOT_FOUND
    

@pytest.mark.django_db
def test_delete_startup_video_anonymous_user(main_startup):
    client = APIClient()

    url = reverse("startup-edit-video", kwargs={"startupId": main_startup.id})

    response = client.delete(url)
   
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ========================================================
# ===================== StartupEditImage =================
# ========================================================

@pytest.mark.django_db
def test_edit_startup_image_successfully(main_user_token, main_startup, mock_upload_file_to_s3):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    
    # Use a simpler and standard file name
    image_content = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF'
        b'\xFF\xFF\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00'
        b'\x01\x00\x00\x02\x02\x4C\x01\x00\x3B'
    )
    image_file = SimpleUploadedFile("test_image.jpg", image_content, content_type="image/jpg")

    payload = {"image": image_file}
    url = reverse("startup-edit-image", kwargs={"startupId": main_startup.id})
    
    with patch('startups.views.utils.upload_file_to_s3', mock_upload_file_to_s3.upload_image_to_s3):
        response = client.put(url, data=payload, format='multipart')
    
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response data: {response.json()}")
    
    # Print out the error details
    if response.status_code != status.HTTP_200_OK:
        logger.error(f"Error details: {response.data}")

    assert response.status_code == status.HTTP_200_OK
    new_image = StartupImage.objects.filter(startup=main_startup,is_active = True)
    assert new_image[0].url == "https://examplebucket.s3.amazonaws.com/media/public/test_image.jpg"

@pytest.mark.django_db
def test_cofunder_edit_startup_image_successfully(main_user_token, third_startup, mock_upload_file_to_s3):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    
    # Use a simpler and standard file name
    image_content = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF'
        b'\xFF\xFF\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00'
        b'\x01\x00\x00\x02\x02\x4C\x01\x00\x3B'
    )
    image_file = SimpleUploadedFile("test_image.jpg", image_content, content_type="image/jpg")

    payload = {"image": image_file}
    url = reverse("startup-edit-image", kwargs={"startupId": third_startup.id})
    
    with patch('startups.views.utils.upload_file_to_s3', mock_upload_file_to_s3.upload_image_to_s3):
        response = client.put(url, data=payload, format='multipart')
    
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response data: {response.json()}")
    
    # Print out the error details
    if response.status_code != status.HTTP_200_OK:
        logger.error(f"Error details: {response.data}")

    assert response.status_code == status.HTTP_200_OK
    new_image = StartupImage.objects.filter(startup=third_startup,is_active = True)
    assert new_image[0].url == "https://examplebucket.s3.amazonaws.com/media/public/test_image.jpg"

@pytest.mark.django_db
def test_edit_startup_image_wrong_id(main_user_token, mock_upload_file_to_s3):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    # Using Image content so django doesnt reject it as a non-image file
    image_content = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF'
        b'\xFF\xFF\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00'
        b'\x01\x00\x00\x02\x02\x4C\x01\x00\x3B'
    )
    image_file = SimpleUploadedFile("test_image.jpg", image_content, content_type="image/jpg") 
    payload = {
        "image": image_file
    }
    url = reverse("startup-edit-image", kwargs={"startupId": FAKE_UUID})
    with patch('startups.views.utils.upload_file_to_s3', mock_upload_file_to_s3):
        response = client.put(url, data=payload, format='multipart')
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_startup_image_anonymous_user(main_startup, mock_upload_file_to_s3):
    client = APIClient()
   # using an image content so that the image can be uploaded
    image_content = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF'
        b'\xFF\xFF\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00'
        b'\x01\x00\x00\x02\x02\x4C\x01\x00\x3B'
    )
    image_file = SimpleUploadedFile("test_image.jpg", image_content, content_type="image/jpg")
    payload = {
        "image":image_file
    }

    url = reverse("startup-edit-image", kwargs={"startupId": main_startup.id})
    with patch('startups.views.utils.upload_file_to_s3', mock_upload_file_to_s3):
        response = client.put(url, data = payload, format='multipart')
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ========================================================
# ===================== StartupEditPitchDeck =============
# ========================================================

@pytest.mark.django_db
def test_edit_startup_pitch_deck_successfully(main_user_token, main_startup, mock_upload_file_to_s3):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    file_content = b'%PDF-1.4\n%ASCII\n1 0 obj\n<<\n/Type /Catalog\n/Outlines 2 0 R\n/Pages 3 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Outlines\n/Count 0\n>>\nendobj\n3 0 obj\n<<\n/Type /Pages\n/Kids [4 0 R]\n/Count 1\n>>\nendobj\n4 0 obj\n<<\n/Type /Page\n/Parent 3 0 R\n/MediaBox [0 0 612 792]\n/Contents 5 0 R\n/Resources <<\n/ProcSet [/PDF /Text]\n>>\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000074 00000 n \n0000000125 00000 n \n0000000190 00000 n \n0000000293 00000 n \ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n358\n%%EOF'
    pitch_deck_file = SimpleUploadedFile("test_pitch_deck.pdf",file_content, content_type="application/pdf")
    payload = {"pitchDeck": pitch_deck_file}

    url = reverse("startup-create-pitchdeck", kwargs={"startupId": main_startup.id})

    with patch('startups.views.utils.upload_file_to_s3', mock_upload_file_to_s3):
        response = client.put(url, data=payload, format='multipart')
    
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response data: {response.json()}")
   
    assert response.status_code == status.HTTP_200_OK
    # Check if response content is JSON
    if 'application/json' in response['Content-Type']:
        response_data = response.json()
        assert response_data.get("message") == "Startup Pitch Deck updated successfully"
    else:
        assert False, f"Response content type is not JSON: {response['Content-Type']}"

    logger.info(f"Response content: {response.content}")
     # Check if response content type is JSON
    content_type = response.get("Content-Type")
    logger.info(f"Response Content-Type: {content_type}")

    assert content_type is not None, "Content-Type header is missing"
    assert "application/json" in content_type, f"Unexpected Content-Type: {content_type}"

    # Parse response data
    response_data = response.json()
    logger.info(f"Response data: {response_data}")

    assert response_data.get("message") == "Startup Pitch Deck updated successfully"

   
    new_pitch_deck = StartupSlidedeck.objects.filter(startup=main_startup,is_active = True)
    assert new_pitch_deck[0].url == "https://examplebucket.s3.amazonaws.com/media/public/test_pitch_deck.pdf"

@pytest.mark.django_db
def test_cofunder_edit_startup_pitch_deck_successfully(main_user_token, third_startup, mock_upload_file_to_s3):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    file_content = b'%PDF-1.4\n%ASCII\n1 0 obj\n<<\n/Type /Catalog\n/Outlines 2 0 R\n/Pages 3 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Outlines\n/Count 0\n>>\nendobj\n3 0 obj\n<<\n/Type /Pages\n/Kids [4 0 R]\n/Count 1\n>>\nendobj\n4 0 obj\n<<\n/Type /Page\n/Parent 3 0 R\n/MediaBox [0 0 612 792]\n/Contents 5 0 R\n/Resources <<\n/ProcSet [/PDF /Text]\n>>\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000074 00000 n \n0000000125 00000 n \n0000000190 00000 n \n0000000293 00000 n \ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n358\n%%EOF'
    pitch_deck_file = SimpleUploadedFile("test_pitch_deck.pdf",file_content, content_type="application/pdf")
    payload = {"pitchDeck": pitch_deck_file}

    url = reverse("startup-create-pitchdeck", kwargs={"startupId": third_startup.id})

    with patch('startups.views.utils.upload_file_to_s3', mock_upload_file_to_s3):
        response = client.put(url, data=payload, format='multipart')
    
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response data: {response.json()}")
   
    assert response.status_code == status.HTTP_200_OK
    # Check if response content is JSON
    if 'application/json' in response['Content-Type']:
        response_data = response.json()
        assert response_data.get("message") == "Startup Pitch Deck updated successfully"
    else:
        assert False, f"Response content type is not JSON: {response['Content-Type']}"

    logger.info(f"Response content: {response.content}")
     # Check if response content type is JSON
    content_type = response.get("Content-Type")
    logger.info(f"Response Content-Type: {content_type}")

    assert content_type is not None, "Content-Type header is missing"
    assert "application/json" in content_type, f"Unexpected Content-Type: {content_type}"

    # Parse response data
    response_data = response.json()
    logger.info(f"Response data: {response_data}")

    assert response_data.get("message") == "Startup Pitch Deck updated successfully"

   
    new_pitch_deck = StartupSlidedeck.objects.filter(startup=third_startup,is_active = True)
    assert new_pitch_deck[0].url == "https://examplebucket.s3.amazonaws.com/media/public/test_pitch_deck.pdf"

@pytest.mark.django_db
def test_edit_startup_pitch_deck_wrong_id(main_user_token, mock_upload_file_to_s3):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    file_content = b'%PDF-1.4\n%ASCII\n1 0 obj\n<<\n/Type /Catalog\n/Outlines 2 0 R\n/Pages 3 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Outlines\n/Count 0\n>>\nendobj\n3 0 obj\n<<\n/Type /Pages\n/Kids [4 0 R]\n/Count 1\n>>\nendobj\n4 0 obj\n<<\n/Type /Page\n/Parent 3 0 R\n/MediaBox [0 0 612 792]\n/Contents 5 0 R\n/Resources <<\n/ProcSet [/PDF /Text]\n>>\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000074 00000 n \n0000000125 00000 n \n0000000190 00000 n \n0000000293 00000 n \ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n358\n%%EOF'
    pitch_deck_file = SimpleUploadedFile("test_pitch_deck.pdf",file_content, content_type="application/pdf")
    
    payload = {
        "pitchDeck": pitch_deck_file
    }
    
    url = reverse("startup-create-pitchdeck", kwargs={"startupId": FAKE_UUID})
    with patch('startups.views.utils.upload_file_to_s3', mock_upload_file_to_s3):
        response = client.put(url, data=payload, format='multipart')
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
 
@pytest.mark.django_db
def test_edit_startup_pitch_deck_anonymous_user(main_startup, mock_upload_file_to_s3):
    client = APIClient()
    file_content = b'%PDF-1.4\n%ASCII\n1 0 obj\n<<\n/Type /Catalog\n/Outlines 2 0 R\n/Pages 3 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Outlines\n/Count 0\n>>\nendobj\n3 0 obj\n<<\n/Type /Pages\n/Kids [4 0 R]\n/Count 1\n>>\nendobj\n4 0 obj\n<<\n/Type /Page\n/Parent 3 0 R\n/MediaBox [0 0 612 792]\n/Contents 5 0 R\n/Resources <<\n/ProcSet [/PDF /Text]\n>>\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000074 00000 n \n0000000125 00000 n \n0000000190 00000 n \n0000000293 00000 n \ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n358\n%%EOF'
    pitch_deck_file = SimpleUploadedFile("test_pitch_deck.pdf",file_content, content_type="application/pdf")
    payload = {
        "pitchDeck":pitch_deck_file
    }
    url = reverse("startup-create-pitchdeck", kwargs={"startupId": main_startup.id})
    with patch('startups.views.utils.upload_file_to_s3', mock_upload_file_to_s3):
        response = client.put(url, data = payload, format='multipart')
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ========================================================
# ===================== StartupEditDescription ===========
# ========================================================    
    

@pytest.mark.django_db
def test_edit_startup_description_successfully(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")  
    payload = {
        "description": TEST_STARTUP_DATA["startup_new_description"]
    }
    url = reverse("startup-edit-description", kwargs={"startupId": main_startup.id})
    response = client.put(url, data = payload, format='json')
    assert response.status_code == status.HTTP_200_OK
    new_query = Startup.objects.get(id= main_startup.id, is_active=True)
    assert new_query.description == TEST_STARTUP_DATA["startup_new_description"]

@pytest.mark.django_db
def test_cofunder_edit_startup_description_successfully(main_user_token, third_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")  
    payload = {
        "description": TEST_STARTUP_DATA["startup_new_description"]
    }
    url = reverse("startup-edit-description", kwargs={"startupId": third_startup.id})
    response = client.put(url, data = payload, format='json')
    assert response.status_code == status.HTTP_200_OK
    new_query = Startup.objects.get(id= third_startup.id, is_active=True)
    assert new_query.description == TEST_STARTUP_DATA["startup_new_description"]


@pytest.mark.django_db
def test_edit_startup_description_wrong_id(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "description":TEST_STARTUP_DATA["startup_new_description"]
    }
    url = reverse("startup-edit-description", kwargs={"startupId": FAKE_UUID})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_startup_description_anonymous_user(main_startup):
    client = APIClient()
    payload = {
        "description":TEST_STARTUP_DATA["startup_new_description"]
    }
    url = reverse("startup-edit-description", kwargs={"startupId": main_startup.id})
    response = client.put(url, data= payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    
# ========================================================
# =============== Get Business Traction ==================
# ========================================================

@pytest.mark.django_db
def test_get_business_traction_success(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": main_startup.id})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["businessModel"] == [StartupBusinessTraction.PRODUCT_SALES]
    assert response.data["businessRevenueSources"] == StartupBusinessTraction.B2B
    assert response.data["mrr"] == FAKE_STARTUP_DATA["mrr"]
    assert len(response.data["topCustomers"]) == 1
    
@pytest.mark.django_db
def test_cofunder_get_business_traction_success(main_user_token, third_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": third_startup.id})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["businessModel"] == [StartupBusinessTraction.PRODUCT_SALES]
    assert response.data["businessRevenueSources"] == StartupBusinessTraction.B2B
    assert response.data["mrr"] == FAKE_STARTUP_DATA["mrr"]

@pytest.mark.django_db
def test_get_business_traction_wrong_starup_id(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId":FAKE_UUID})
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_get_business_traction_not_authorized(main_user_token, second_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": second_startup.id})
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_get_business_traction_anonymous_user(main_startup):
    client = APIClient()
    
    url = reverse("business-traction", kwargs={"startupId": main_startup.id})
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ========================================================
# ============== Create Business Traction ================
# ========================================================


@pytest.mark.django_db
def test_create_business_traction_success(main_user_token, second_startup):
    token = main_user_token.get("secondary_token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": second_startup.id})
    data = {
        "businessModel": [StartupBusinessTraction.E_COMMERCE],
        "businessRevenueSources": StartupBusinessTraction.B2C,
        "mrr": 1000,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"},
            {"name": "Customer 2", "url": "http://example.com/customer2"}
        ]
    }
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    business_traction = StartupBusinessTraction.objects.filter(startup=second_startup)
    assert business_traction.exists()
    assert business_traction[0].business_model == StartupBusinessTraction.E_COMMERCE
    assert business_traction[0].business_revenue_sources ==  data["businessRevenueSources"]
    assert business_traction[0].mrr ==  data["mrr"]
    top_customer = StartupTopCustomer.objects.filter(startup=second_startup,business_traction= business_traction[0])
    assert len(top_customer) == 2


@pytest.mark.django_db
def test_create_business_traction_three_business_models(main_user_token, second_startup):
    token = main_user_token.get("secondary_token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": second_startup.id})
    data = {
        "businessModel": [StartupBusinessTraction.E_COMMERCE, StartupBusinessTraction.PRODUCT_SALES, StartupBusinessTraction.SERVICE_BASED],
        "businessRevenueSources": StartupBusinessTraction.B2C,
        "mrr": 1000,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"},
            {"name": "Customer 2", "url": "http://example.com/customer2"}
        ]
    }
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    business_traction = StartupBusinessTraction.objects.filter(startup=second_startup)
    assert business_traction.exists()
    assert business_traction[0].business_model == f'{StartupBusinessTraction.E_COMMERCE},{StartupBusinessTraction.PRODUCT_SALES},{StartupBusinessTraction.SERVICE_BASED}'
    assert business_traction[0].business_revenue_sources ==  data["businessRevenueSources"]
    assert business_traction[0].mrr ==  data["mrr"]
    top_customer = StartupTopCustomer.objects.filter(startup=second_startup,business_traction= business_traction[0])
    assert len(top_customer) == 2

@pytest.mark.django_db
def test_cofunder_create_business_traction_success(main_user_token, third_startup):
    token = main_user_token.get("secondary_token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    StartupBusinessTraction.objects.filter(startup=third_startup).delete()
    
    url = reverse("business-traction", kwargs={"startupId": third_startup.id})
    data = {
        "businessModel": [StartupBusinessTraction.E_COMMERCE],
        "businessRevenueSources": StartupBusinessTraction.B2C,
        "mrr": 1000,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"},
            {"name": "Customer 2", "url": "http://example.com/customer2"}
        ]
    }
    response = client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    business_traction = StartupBusinessTraction.objects.filter(startup=third_startup)
    assert business_traction.exists()
    assert business_traction[0].business_model == StartupBusinessTraction.E_COMMERCE
    assert business_traction[0].business_revenue_sources ==  data["businessRevenueSources"]
    assert business_traction[0].mrr ==  data["mrr"]
    top_customer = StartupTopCustomer.objects.filter(startup=third_startup,business_traction= business_traction[0])
    assert len(top_customer) == 2


@pytest.mark.django_db
def test_create_business_traction_wrong_payload(main_user_token, second_startup):
    token = main_user_token.get("secondary_token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": second_startup.id})
    data = {
        "businessModel": "tec",
        "businessRevenueSources": StartupBusinessTraction.B2C,
        "mrr": 1000,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"},
            {"name": "Customer 2", "url": "http://example.com/customer2"}
        ]
    }
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_business_traction_empty_top_customers(main_user_token, second_startup):
    token = main_user_token.get("secondary_token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": second_startup.id})
    data = {
        "businessModel": [StartupBusinessTraction.E_COMMERCE],
        "businessRevenueSources": StartupBusinessTraction.B2C,
        "mrr": 1000,
        "topCustomers": []
    }
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    business_traction = StartupBusinessTraction.objects.filter(startup=second_startup)
    assert business_traction.exists()
    assert business_traction[0].business_model == StartupBusinessTraction.E_COMMERCE
    assert business_traction[0].business_revenue_sources ==  data["businessRevenueSources"]
    assert business_traction[0].mrr ==  data["mrr"]
    top_customer = StartupTopCustomer.objects.filter(startup=second_startup,business_traction= business_traction[0])
    assert len(top_customer) == 0

@pytest.mark.django_db
def test_create_business_traction_already_exists(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": main_startup.id})
    data = {
        "businessModel": [StartupBusinessTraction.E_COMMERCE],
        "businessRevenueSources": StartupBusinessTraction.B2C,
        "mrr": 1000,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"},
            {"name": "Customer 2", "url": "http://example.com/customer2"}
        ]
    }
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_business_traction_startup_not_exists(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": FAKE_UUID})
    data = {
        "businessModel": [StartupBusinessTraction.E_COMMERCE],
        "businessRevenueSources": StartupBusinessTraction.B2C,
        "mrr": 1000,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"},
            {"name": "Customer 2", "url": "http://example.com/customer2"}
        ]
    }
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_create_business_traction_anonymous_user(second_startup):
    client = APIClient()
    
    url = reverse("business-traction", kwargs={"startupId": second_startup.id})
    data = {
        "businessModel": [StartupBusinessTraction.E_COMMERCE],
        "businessRevenueSources": StartupBusinessTraction.B2C,
        "mrr": 1000,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"},
            {"name": "Customer 2", "url": "http://example.com/customer2"}
        ]
    }
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ========================================================
# =============== Edit Business Traction =================
# ========================================================

@pytest.mark.django_db
def test_edit_business_traction_success(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": main_startup.id})
    data = {
        "businessModel": [StartupBusinessTraction.MARKETPLACE],
        "businessRevenueSources": StartupBusinessTraction.B2B2C,
        "mrr": 1001,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"}
        ]
    }
    response = client.put(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    
    business_traction = StartupBusinessTraction.objects.filter(startup=main_startup)
    
    assert business_traction.exists()
    assert business_traction[0].business_model == StartupBusinessTraction.MARKETPLACE
    assert business_traction[0].business_revenue_sources ==  data["businessRevenueSources"]
    assert business_traction[0].mrr ==  data["mrr"]
    top_customer = StartupTopCustomer.objects.filter(startup=main_startup,business_traction= business_traction[0])
    assert len(top_customer) == 1

@pytest.mark.django_db
def test_cofunder_edit_business_traction_success(main_user_token, third_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": third_startup.id})
    data = {
        "businessModel": [StartupBusinessTraction.MARKETPLACE],
        "businessRevenueSources": StartupBusinessTraction.B2B2C,
        "mrr": 1001,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"}
        ]
    }
    response = client.put(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    
    business_traction = StartupBusinessTraction.objects.filter(startup=third_startup)
    
    assert business_traction.exists()
    assert business_traction[0].business_model == StartupBusinessTraction.MARKETPLACE
    assert business_traction[0].business_revenue_sources ==  data["businessRevenueSources"]
    assert business_traction[0].mrr ==  data["mrr"]
    top_customer = StartupTopCustomer.objects.filter(startup=third_startup,business_traction= business_traction[0])
    assert len(top_customer) == 1

@pytest.mark.django_db
def test_edit_business_traction_wrong_payload(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": main_startup.id})
    data = {
        "businessModel": "tec",
        "businessRevenueSources": StartupBusinessTraction.B2B2C,
        "mrr": 1001,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"}
        ]
    }
    response = client.put(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_edit_business_not_authorized(main_user_token, second_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": second_startup.id})
    data = {
        "businessModel": [StartupBusinessTraction.MARKETPLACE],
        "businessRevenueSources": StartupBusinessTraction.B2B2C,
        "mrr": 1001,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"}
        ]
    }
    response = client.put(url, data, format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_business_traction_not_exists(main_user_token, second_startup):
    token = main_user_token.get("secondary_token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("business-traction", kwargs={"startupId": second_startup.id})
    data = {
        "businessModel": [StartupBusinessTraction.MARKETPLACE],
        "businessRevenueSources": StartupBusinessTraction.B2B2C,
        "mrr": 1001,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"}
        ]
    }
    response = client.put(url, data, format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_business_traction_anonymous_user(main_startup):
    client = APIClient()
    
    url = reverse("business-traction", kwargs={"startupId": main_startup.id})
    data = {
        "businessModel": [StartupBusinessTraction.MARKETPLACE],
        "businessRevenueSources": StartupBusinessTraction.B2B2C,
        "mrr": 1001,
        "topCustomers": [
            {"name": "Customer 1", "url": "http://example.com/customer1"}
        ]
    }
    response = client.put(url, data, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    

# ========================================================
# ================== Share StarUp ========================
# ========================================================

@pytest.mark.django_db
def test_share_public_startup_success(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    new_query = Startup.objects.get(id=main_startup.id)
    new_query.is_public = True
    new_query.save()
    
    url = reverse("share", kwargs={"startupId": main_startup.id})
    data = {
        'firstName': 'Johnatan',
        'lastName': 'Dane',
        'email': 'johndoe33@example.com',
        'relationship': 'Friend'
    }
    response = client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert StartupShare.objects.filter(startup_id=main_startup.id, email='johndoe33@example.com').exists()


@pytest.mark.django_db
def test_share_private_startup_success(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    url = reverse("share", kwargs={"startupId": main_startup.id})
    data = {
        'firstName': 'Johnatan',
        'lastName': 'Dane',
        'email': 'johndoe33@example.com',
        'relationship': 'Friend'
    }
    response = client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert StartupShare.objects.filter(startup_id=main_startup.id, email='johndoe33@example.com').exists()
    assert PrivateVisitor.objects.filter(email='johndoe33@example.com', startup_id=main_startup.id).exists()

@pytest.mark.django_db
def test_public_startup_share_home_with_repeated_email(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    new_query = Startup.objects.get(id=main_startup.id)
    new_query.is_public = True
    new_query.save()
    
    url = reverse("share", kwargs={"startupId": main_startup.id})
    data = {
        'firstName': 'Johnatan',
        'lastName': 'Dane',
        'email': 'johndoe33@example.com',
        'relationship': 'Friend'
    }
    client.post(url, data, format="json")
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get('error') == 'You have already shared to this email'

@pytest.mark.django_db
def test_share_startup_bad_request(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("share", kwargs={"startupId": main_startup.id})
    data = {
        'firstName': '',
        'lastName': 'Dane',
        'email': 'johndoe33@example.com',
        'relationship': 'Friend'
    }
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_share_startup_anonymous_user(main_startup):
    client = APIClient()
    
    url = reverse("business-traction", kwargs={"startupId": main_startup.id})
    data = {
       'firstName': 'Johnatan',
        'lastName': 'Dane',
        'email': 'johndoe33@example.com',
        'relationship': 'Friend'
    }
    response = client.put(url, data, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
# ========================================================
# ==================== Check Visitors ====================
# ========================================================

@pytest.mark.django_db
def test_check_vistor_startup_new_visitor_success(main_startup):
    client = APIClient()
    id_divice = uuid.uuid4().int
    
    new_query = Startup.objects.get(id=main_startup.id)
    new_query.is_public = True
    new_query.save()

    headers = {'HTTP_X_DEVICE_ID': id_divice}
    url = reverse("check-public-visitor", kwargs={"startupId": main_startup.id})
   
    response = client.get(url, **headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("new_visitor") == True
    
@pytest.mark.django_db
def test_check_vistor_startup_visitor_already_exist_success(main_startup):
    client = APIClient()
    id_divice = uuid.uuid4().int
    
    new_query = Startup.objects.get(id=main_startup.id)
    new_query.is_public = True
    new_query.save()
    
    PublicVisitor.objects.create(
        device_id = id_divice,
        startup = main_startup
    )

    headers = {'HTTP_X_DEVICE_ID': id_divice}
    url = reverse("check-public-visitor", kwargs={"startupId": main_startup.id})
   
    response = client.get(url, **headers)
    
    assert response.status_code == status.HTTP_200_OK
    

@pytest.mark.django_db
def test_check_vistor_startup_missing_device_id(main_startup):
    client = APIClient()

    new_query = Startup.objects.get(id=main_startup.id)
    new_query.is_public = True
    new_query.save()

    url = reverse("check-public-visitor", kwargs={"startupId": main_startup.id})

    response = client.get(url)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("error") == "Device id not found"

@pytest.mark.django_db
def test_check_vistor_startup_nonexistent_startup():
    client = APIClient()
    id_divice = uuid.uuid4().int

    headers = {'HTTP_X_DEVICE_ID': id_divice}

    url = reverse("check-public-visitor", kwargs={"startupId": FAKE_UUID})

    response = client.get(url, **headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("error") == "Startup does not exist"


# ========================================================
# ================== Public Generic View =================
# ========================================================

@pytest.mark.django_db
def test_create_visitor_new_visitor(main_startup):
    client = APIClient()
    id_divice = uuid.uuid4().int

    new_query = Startup.objects.get(id=main_startup.id)
    new_query.is_public = True
    new_query.save()

    headers = {'HTTP_X_DEVICE_ID': id_divice}
    url = reverse("public-view", kwargs={"startupId": main_startup.id})
    data = {"email": "newvisitor@example.com", "isTermsAcepted": True}

    response = client.post(url, data, format='json', **headers)

    assert response.status_code == status.HTTP_200_OK
    assert PublicVisitor.objects.filter(email="newvisitor@example.com", startup=main_startup).exists()
    

@pytest.mark.django_db
def test_create_visitor_already_exists(main_startup):
    client = APIClient()
    id_divice = uuid.uuid4().int

    new_query = Startup.objects.get(id=main_startup.id)
    new_query.is_public = True
    new_query.save()

    email = "test@example.com"
    PublicVisitor.objects.create(
        email=email,
        startup=main_startup,
        device_id=id_divice,
        is_terms_acepted=True
    )

    headers = {'HTTP_X_DEVICE_ID': id_divice}
    url = reverse("public-view", kwargs={"startupId": main_startup.id})
    data = {"email": email, "isTermsAcepted": True}

    response = client.post(url, data, format='json', **headers)

    assert response.status_code == status.HTTP_200_OK
    
@pytest.mark.django_db
def test_create_visitor_missing_device_id(main_startup):
    client = APIClient()

    url = reverse("public-view", kwargs={"startupId": main_startup.id})
    data = {"email": "test@example.com", "isTermsAcepted": True}

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("error") == "Device id not found"

@pytest.mark.django_db
def test_create_visitor_invalid_data(main_startup):
    client = APIClient()
    id_divice = uuid.uuid4().int

    headers = {'HTTP_X_DEVICE_ID': id_divice}
    url = reverse("public-view", kwargs={"startupId": main_startup.id})
    data = {"email": "invalid-email", "isTermsAcepted": True}

    response = client.post(url, data, format='json', **headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.json().get("errors")

@pytest.mark.django_db
def test_create_visitor_terms_not_accepted(main_startup):
    client = APIClient()
    id_divice = uuid.uuid4().int

    headers = {'HTTP_X_DEVICE_ID': id_divice}
    url = reverse("public-view", kwargs={"startupId": main_startup.id})
    data = {"email": "test@example.com", "isTermsAcepted": False}

    response = client.post(url, data, format='json', **headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("error") == "Terms and conditions must be accepted"
    
@pytest.mark.django_db
def test_create_visitor_nonexistent_startup():
    client = APIClient()
    id_divice = uuid.uuid4().int

    headers = {'HTTP_X_DEVICE_ID': id_divice}
    
    url = reverse("public-view", kwargs={"startupId": FAKE_UUID})
    data = {"email": "test@example.com", "isTermsAcepted": True}

    response = client.post(url, data, format='json', **headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("error") == "Startup does not exist"

# ========================================================
# ================= Private Generic View =================
# ========================================================

@pytest.mark.django_db
def test_private_view_success(main_startup):
    client = APIClient()
    id_divice = uuid.uuid4().int

    email = "test@example.com"
    token = uuid.uuid4().int
    PrivateVisitor.objects.create(
        email=email,
        unique_token=token,
        startup=main_startup
    )
    headers = {'HTTP_X_DEVICE_ID': id_divice}
    url = reverse("private-view", kwargs={"startupId": main_startup.id, "email": email, "token": token})
    data = {"email": email, "isTermsAcepted": True}
    response = client.post(url, data, format='json', **headers)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_private_view_startup_does_not_exist(main_startup):
    client = APIClient()
    id_divice = uuid.uuid4().int

    email = "test@example.com"
    token = uuid.uuid4().int
   
    PrivateVisitor.objects.create(
        email=email,
        unique_token=token,
        startup=main_startup
    )
    headers = {'HTTP_X_DEVICE_ID': id_divice}
    url = reverse("private-view", kwargs={"startupId": FAKE_UUID, "email": email, "token": token})
    data = {"email": email, "isTermsAcepted": True}
    response = client.post(url, data, format='json', **headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("error") == "Startup does not exist"

@pytest.mark.django_db
def test_private_view_private_visitor_does_not_exist(main_startup):
    client = APIClient()
    id_divice = uuid.uuid4().int
    email = "nonexistent@example.com"
    token = 99999
    url = reverse("private-view", kwargs={"startupId": main_startup.id, "email": email, "token": token})
    headers = {'HTTP_X_DEVICE_ID': id_divice}
    data = {"email": "test@example.com", "isTermsAcepted": True}
    response = client.post(url, data, format='json', **headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("error") == "PrivateVisitor does not exist"


# ========================================================
# =============== EDIT STARTUP PRIVACY ===================
# ========================================================

@pytest.mark.django_db
def test_edit_startup_privacy_success(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "isPrivacy":False
    }
    url = reverse("startup-edit-privacy", kwargs={"startupId": main_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code ==status.HTTP_200_OK
    new_query = Startup.objects.get(id= main_startup.id, is_active=True )
    assert new_query.is_public == False

@pytest.mark.django_db
def test_cofunder_edit_startup_privacy_success(main_user_token, third_startup  ):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "isPrivacy":False
    }
    url = reverse("startup-edit-privacy", kwargs={"startupId": third_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code ==status.HTTP_200_OK
    new_query = Startup.objects.get(id=third_startup.id, is_active=True )
    assert new_query.is_public == False
    
@pytest.mark.django_db
def test_edit_startup_privacy_wrong_id(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {"isPrivacy":False}
    url = reverse("startup-edit-privacy", kwargs={"startupId": FAKE_UUID})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_startup_privacy_not_authorized(main_user_token,second_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    payload = {"isPrivacy":False}
    url = reverse("startup-edit-privacy", kwargs={"startupId": second_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_edit_startup_privacy_anonymous_user(main_startup):
    client = APIClient()
    payload = {"isPrivacy":False}
    url = reverse("startup-edit-privacy", kwargs={"startupId": main_startup.id})
    response = client.put(url, data = payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ========================================================
# ============ GET CATEGORY INDUSTRIE LIST ===============
# ========================================================

