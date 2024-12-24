from django.urls import path
from .views import LocationListView

urlpatterns = [
    path('location', LocationListView.as_view(), name='location-list')
]