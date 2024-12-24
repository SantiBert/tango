from django.urls import path
from .views import CreateReviewView



urlpatterns = [
    path('reviews/<str:startupId>/create/',CreateReviewView.as_view(),name="review-create")
]
