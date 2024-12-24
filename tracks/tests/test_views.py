import pytest

from rest_framework.test import APIClient
from rest_framework import status

from django.urls import reverse

from users.tests.fixtures import common_user_token
from startups.tests.fixtures import common_startup

main_user_token = common_user_token
main_startup = common_startup


# ========================================================
# =============== Edit Business Traction =================
# ========================================================

"""
@pytest.mark.django_db
def test_track_event_success(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("track-event")
    data = {
            'event_name': 'Test Event',
            'distinct_id': 'user123',
            'properties': {'property1': 'value1', 'property2': 'value2'}
        }
    
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
""" 

@pytest.mark.django_db
def test_track_event_wrong_payload(main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse("track-event")
    data = {
            'distinct_id': 'user123',
            }
    
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST