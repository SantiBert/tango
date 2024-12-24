from django.urls import path
from .views import(
    CreateStripeCheckoutSessionView,
    CreateStartupBillingPortalSessionView,
    StripeWebhookView
)
urlpatterns = [
path('startup/<str:startupId>/create-checkout-session/',CreateStripeCheckoutSessionView.as_view(),name="create-checkout-session"),
path('startup/<str:startupId>/create-billing-portal-session/',CreateStartupBillingPortalSessionView.as_view(),name="create-billing-portal-session"),
path('webhooks/', StripeWebhookView.as_view(), name='stripe-webhook'),
]