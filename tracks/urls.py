from django.urls import path
from .views import (
    TrackEventView,
    InitialTackDashBoardView
    )

urlpatterns = [
    path('track-event/', TrackEventView.as_view(), name='track-event'),
    path('initial-dashboard/',InitialTackDashBoardView.as_view(), name='initial-dashboard')
]
