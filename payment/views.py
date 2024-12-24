import stripe
import logging
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from users.permissions import IsRegistered
from startups.models import Startup
from rest_framework.response import Response
from rest_framework import generics, status
from .models import Subscription

logger = logging.getLogger(__name__)

class CreateStripeCheckoutSessionView(generics.GenericAPIView):
    permission_classes = [IsRegistered]

    def get(self, request, startupId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId,main_founder_id=user.id,is_active=True)
            
            if not startup:
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            
            plan_type = request.query_params.get('plan', 'monthly').lower()  

            # Check if the plan is valid (only 'monthly' or 'annual')
            if plan_type not in ['monthly', 'annual']:
                return Response({"error": "Invalid plan type. It must be either 'monthly' or 'annual'."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Assign the price_id based on plan type
            if plan_type == 'annual':
                price_id = settings.PRO_ANNUAL_ID 
            else:
                price_id = settings.PRO_MONTHLY_ID  

            stripe.api_key = settings.STRIPE_SECRET_KEY
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=f'https://{settings.MAIN_DOMAIN}/startup/pro/successpage',
                cancel_url=f'https://{settings.MAIN_DOMAIN}/startup/pro/cancelpage',
                metadata={'startup_id': startupId}
            )

            return Response({
                'sessionId': checkout_session['id'],
                'url': checkout_session['url']
            })

        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            body = e.json_body
            err  = body.get('error', {})
            print(err)
            logger.error(f"Stripe error: {err.get('message')}, Type: {err.get('type')}, Code: {err.get('code')}, Param: {err.get('param')}")
            return Response({"error": "Stripe error occurred. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Server error: {e}")
            return Response({"error": "An unexpected error occurred. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateStartupBillingPortalSessionView(generics.GenericAPIView):
    permission_classes = [IsRegistered]

    def get(self, request, startupId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId,main_founder_id=user.id,is_active=True)
            
            subscription = Subscription.objects.get(startup=startup, stripe_subscription_status__in=[Subscription.TRIAL, Subscription.BASIC])
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=f'https://{settings.MAIN_DOMAIN}'
            )

            return Response({'url': session.url})

        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Subscription.DoesNotExist:
            return Response({"error": "No active subscription found"}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            body = e.json_body
            err  = body.get('error', {})
            logger.error(f"Stripe error: {err.get('message')}, Type: {err.get('type')}, Code: {err.get('code')}, Param: {err.get('param')}")
            return Response({"error": "Stripe error occurred. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Server error: {e}")
            return Response({"error": "An unexpected error occurred. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(generics.GenericAPIView):
    
    permission_classes = ()
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.DJSTRIPE_WEBHOOK_SECRET

        if not sig_header:
            logger.error("Missing Stripe signature header.")
            return HttpResponse("Missing signature header", status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the event by building it with Stripe signature
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            return HttpResponse("Invalid payload", status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            return HttpResponse("Invalid signature", status=status.HTTP_400_BAD_REQUEST)

        # Handle only the event `customer.subscription.updated`
        if event['type'] == 'customer.subscription.updated':
            session = event['data']['object']
            customer_id = session.get('customer')
            subscription_id = session.get('id')
            subscription_status = session.get('status')
            metadata = session.get('metadata', {})

            try:
                startup_id = metadata.get('startup_id')
                if not startup_id:
                    logger.error(f"Startup ID missing in session metadata for customer {customer_id}")
                    return HttpResponse("Missing startup ID in metadata", status=status.HTTP_400_BAD_REQUEST)

                startup = Startup.objects.get(id=startup_id)

                subscription = Subscription.objects.get(
                    startup=startup,
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription_id
                )
                
                if subscription_status == 'active':
                    subscription.stripe_subscription_status = Subscription.PRO
                elif subscription_status == 'canceled':
                    current_period_end = session.get('current_period_end')
                    current_period_end_datetime = timezone.make_aware(
                        timezone.datetime.fromtimestamp(current_period_end)
                    )

                    if current_period_end_datetime > timezone.now():
                        subscription.stripe_subscription_status = Subscription.PRO
                    else:
                        subscription.stripe_subscription_status = Subscription.BASIC

                subscription.save()

            except Startup.DoesNotExist:
                logger.error(f"Startup with ID {startup_id} does not exist")
                return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
            except Subscription.DoesNotExist:
                logger.error(f"Subscription for customer {customer_id} does not exist")
                return Response({"error": "Subscription does not exist"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error handling subscription for customer {customer_id}: {e}")
                return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            # Log unhandled events
            logger.info(f"Unhandled event type: {event['type']}")
            # Simply return 200 OK for events that are not explicitly handled
            return HttpResponse(status=status.HTTP_200_OK)

        return HttpResponse(status=status.HTTP_200_OK)