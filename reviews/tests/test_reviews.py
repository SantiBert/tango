import pytest

from rest_framework.test import APIClient
from rest_framework import status

from django.urls import reverse

from users.tests.fixtures import (
    common_user_token, 
    common_user_founder
    )
from startups.tests.fixtures import (
    common_startup, 
    common_secondary_startup
    )

from reviews.models import Review

main_user_token = common_user_token
second_user = common_user_founder
main_startup = common_startup
second_startup = common_secondary_startup

PAYLOAD_DATA = {
    'email': 'test@gmail.com',
    'overalRating': 4,
    'teamValue': 5,
    'problemValue': 3,
    'solutionValue': 4,
    'gtmstrategyValue': 5,
    'marketoppValue': 4,
    'details': 'This is a test review',
    'isAnonymous': True
}

FAKE_UUID = 'a8098c1a-f86e-11da-bd1a-00112444be1e'

# ========================================================
# ================= CREATE REVIEW ========================
# ========================================================

@pytest.mark.django_db
def test_create_review_successfully(second_startup):
    client = APIClient()
    email = PAYLOAD_DATA['email']
    
    data = {
        'email':email,
        'overalRating': PAYLOAD_DATA['overalRating'],
        'teamValue': PAYLOAD_DATA['teamValue'],
        'problemValue': PAYLOAD_DATA['problemValue'],
        'solutionValue': PAYLOAD_DATA['solutionValue'],
        'gtmstrategyValue': PAYLOAD_DATA['gtmstrategyValue'],
        'marketoppValue': PAYLOAD_DATA['marketoppValue'],
        'details': PAYLOAD_DATA['details'],
        'isAnonymous': PAYLOAD_DATA['isAnonymous']
    }
    
    url = reverse("review-create",kwargs={"startupId": second_startup.id})
    response = client.post(url, data,format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert Review.objects.filter(email=email,startup=second_startup).exists()


@pytest.mark.django_db
def test_create_duplicate_review(second_startup):
    client = APIClient()
    
    Review.objects.create(
        email = PAYLOAD_DATA['email'],
        startup=second_startup,
        overal_rating=PAYLOAD_DATA['overalRating'],
        team_value=PAYLOAD_DATA['teamValue'],
        problem_value=PAYLOAD_DATA['problemValue'],
        solution_value=PAYLOAD_DATA['solutionValue'],
        gtmstrategy_value=PAYLOAD_DATA['gtmstrategyValue'],
        marketopp_value=PAYLOAD_DATA['marketoppValue'],
        details=PAYLOAD_DATA['details'],
        is_anonymous=PAYLOAD_DATA['isAnonymous']
    )
    
   
    data = {
        'email': PAYLOAD_DATA['email'],
        'overalRating': PAYLOAD_DATA['overalRating'],
        'teamValue': PAYLOAD_DATA['teamValue'],
        'problemValue': PAYLOAD_DATA['problemValue'],
        'solutionValue': PAYLOAD_DATA['solutionValue'],
        'gtmstrategyValue': PAYLOAD_DATA['gtmstrategyValue'],
        'marketoppValue': PAYLOAD_DATA['marketoppValue'],
        'details': PAYLOAD_DATA['details'],
        'isAnonymous': PAYLOAD_DATA['isAnonymous']
    }
    
    url = reverse("review-create",kwargs={"startupId": second_startup.id})
    response = client.post(url, data,format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_review_wrong_payload(second_startup):
    client = APIClient()
    
    data = {
        'email':PAYLOAD_DATA['email'],
        'overalRating':"Wrong string",
        'teamValue': PAYLOAD_DATA['teamValue'],
        'problemValue': PAYLOAD_DATA['problemValue'],
        'solutionValue': PAYLOAD_DATA['solutionValue'],
        'gtmstrategyValue': PAYLOAD_DATA['gtmstrategyValue'],
        'marketoppValue': PAYLOAD_DATA['marketoppValue'],
        'details': PAYLOAD_DATA['details'],
        'isAnonymous': PAYLOAD_DATA['isAnonymous']
    }
    
    url = reverse("review-create",kwargs={"startupId": second_startup.id})
    response = client.post(url, data,format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_review_wrong_id():
    client = APIClient()
    
    data = {
        'email': PAYLOAD_DATA['email'],
        'overalRating': PAYLOAD_DATA['overalRating'],
        'teamValue': PAYLOAD_DATA['teamValue'],
        'problemValue': PAYLOAD_DATA['problemValue'],
        'solutionValue': PAYLOAD_DATA['solutionValue'],
        'gtmstrategyValue': PAYLOAD_DATA['gtmstrategyValue'],
        'marketoppValue': PAYLOAD_DATA['marketoppValue'],
        'details': PAYLOAD_DATA['details'],
        'isAnonymous': PAYLOAD_DATA['isAnonymous']
    }
    
    url = reverse("review-create",kwargs={"startupId": FAKE_UUID})
    response = client.post(url, data,format='json')

    assert response.status_code == status.HTTP_404_NOT_FOUND
