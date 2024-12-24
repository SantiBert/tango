import logging
import math
from datetime import timedelta
from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from django.db import transaction
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from pjbackend import utils

from .models import (
    InvestmentRound, 
    InvestorUser, 
    InversorTemporal,
    FavoriteInvestorsTemporal
    )
from startups.models import Startup, StartupCategory, StartupBusinessTraction, StartupLocation
from users.permissions import IsRegistered

from .serializers import (
    InvestmentRoundSerializer, 
    CreateInvestmentRoundSerializer,
    InvestmentRoundChangeAmountSerializer,
    InvestmentRoundChangeRaisedAmountSerializer, 
    CreateInvestorUserSerializer,
    EditInvestorinParticularRoundSerializer,
    InversorTemporalSerializer,
    FavoriteInvestorsTemporalSerializer
    )

from .filters import InversorTemporalFilter

logger = logging.getLogger(__name__)

class InvestmentRoundView(generics.GenericAPIView):
    serializer_class = CreateInvestmentRoundSerializer
    permission_classes = [IsRegistered]

    def get(self, request, startupId):
        try:
            user = self.request.user
            startup = Startup.objects.get(id=startupId, is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            investors = InvestmentRound.objects.filter(startup=startup, is_active=True)
            serializer = InvestmentRoundSerializer(investors, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, startupId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId, is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            round_type = serializer.validated_data["roundType"]
            amount = serializer.validated_data["amount"]
            raised_amount = serializer.validated_data["raisedAmount"]
            date = serializer.validated_data["date"]
            investors = serializer.validated_data["investors"]
            
            round = InvestmentRound.objects.create(
                startup = startup,
                round_type = round_type,
                amount = amount,
                raised_amount = raised_amount,
                date = date
            )
            for investor in investors:
                first_name = investor.get('firstName')
                last_name = investor.get('lastName')
                firm_name = investor.get('firmName')
                email = investor.get('email')
                amount_invested = investor.get('amountInvested')
                invested_type = investor.get('investedType')
                
                user_investment = InvestorUser.objects.create(
                    round = round,
                    first_name=first_name,
                    last_name =last_name,
                    firm_name = firm_name,
                    email=email,
                    amount_invested =amount_invested,
                    invested_type = invested_type
                    )
                url_in_request = reverse('investments-confirm', kwargs={'startupId': startupId, 'userInvestmentId': user_investment.id})
                accept_link = request.build_absolute_uri(url_in_request) + '?confirm=true'
                decline_link = request.build_absolute_uri(url_in_request) + '?confirm=false'
                utils.send_investors_invite_email(
                    user_investment.email,
                    startup.name,
                    user_investment.first_name,
                    user_investment.last_name,
                    user_investment.firm_name,
                    invested_type,
                    amount_invested,
                    amount,
                    startup.industry_category.name,
                    accept_link,
                    decline_link
                    )
            return Response(status=status.HTTP_201_CREATED)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)     

    def put(self, request, startupId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId, is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            round_type = serializer.validated_data["roundType"]
            amount = serializer.validated_data["amount"]
            raised_amount = serializer.validated_data["raisedAmount"]
            date = serializer.validated_data["date"]
            investors = serializer.validated_data["investors"]
            
            round = InvestmentRound.objects.create(
                startup = startup,
                round_type = round_type,
                amount = amount,
                raised_amount = raised_amount,
                date = date
            )
            for investor in investors:
                first_name = investor.get('firstName')
                last_name = investor.get('lastName')
                firm_name = investor.get('firmName')
                email = investor.get('email')
                amount_invested = investor.get('amountInvested')
                invested_type = investor.get('investedType')
                
                user_investment = InvestorUser.objects.create(
                    round = round,
                    first_name=first_name,
                    last_name =last_name,
                    firm_name = firm_name,
                    email=email,
                    amount_invested =amount_invested,
                    invested_type = invested_type
                    )
                url_in_request = reverse('investments-confirm', kwargs={'startupId': startupId, 'userInvestmentId': user_investment.id})
                accept_link = request.build_absolute_uri(url_in_request) + '?confirm=true'
                decline_link = request.build_absolute_uri(url_in_request) + '?confirm=false'
                utils.send_investors_invite_email(
                    user_investment.email,
                    startup.name,
                    user_investment.first_name,
                    user_investment.last_name,
                    user_investment.firm_name,
                    invested_type,
                    amount_invested,
                    amount,
                    startup.industry_category.name,
                    accept_link,
                    decline_link
                    )
            return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  

class InvestmentRoundConfirmView(generics.GenericAPIView):
    permission_classes = ()

    def get(self, request, startupId, userInvestmentId):
        try:
            confirm = request.query_params.get('confirm', '').lower()
            if confirm == 'true':
                confirm_bool = True
            elif confirm == 'false':
                confirm_bool = False
            else:
                return HttpResponse("<h1>Error</h1><p>Invalid parameter.</p>", status=status.HTTP_400_BAD_REQUEST)
            
            startup = Startup.objects.get(id=startupId, is_active=True)
            investor_user = InvestorUser.objects.get(id=userInvestmentId)

            if investor_user.is_verificated == InvestorUser.VERIFIED:
                return HttpResponse("<h1>Error</h1><p>Has already been confirmed.</p>", status=status.HTTP_400_BAD_REQUEST)
            
            investor_user.is_verificated = InvestorUser.VERIFIED if confirm_bool else InvestorUser.NOT_VERIFIED
            investor_user.save()

            success_message = f"<h1>Success</h1><p>Now you are an Investor of {startup.name}.</p>"
            return HttpResponse(success_message, status=status.HTTP_200_OK)

        except Startup.DoesNotExist:
            return HttpResponse("<h1>Error</h1><p>Startup does not exist.</p>", status=status.HTTP_404_NOT_FOUND)
        except InvestorUser.DoesNotExist:
            return HttpResponse("<h1>Error</h1><p>Investor does not exist.</p>", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return HttpResponse(f"<h1>Error</h1><p>Server error: {str(e)}</p>", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        
    
class InvestmentChangeAmountView(generics.GenericAPIView):
    serializer_class = InvestmentRoundChangeAmountSerializer
    permission_classes = [IsRegistered]

    def put(self, request, startupId, investmentId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                serializer = self.get_serializer(data=request.data)
                round = InvestmentRound.objects.get(
                    id=investmentId,
                    startup = startup,
                    is_active= True
                )
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                
                round.amount  = serializer.validated_data["amount"]
                round.save()
            return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except InvestmentRound.DoesNotExist:
            return Response({"error": "InvestmentRound does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  

class InvestmentChangeRaisedAmountView(generics.GenericAPIView):
    serializer_class = InvestmentRoundChangeRaisedAmountSerializer
    permission_classes = [IsRegistered]

    def put(self, request, startupId, investmentId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                serializer = self.get_serializer(data=request.data)
                round = InvestmentRound.objects.get(
                    id=investmentId,
                    startup = startup,
                    is_active= True
                )
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                
                round.raised_amount = serializer.validated_data["raisedAmount"]
                round.save()
            return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except InvestmentRound.DoesNotExist:
            return Response({"error": "InvestmentRound does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  

class DeleteInvestmentRound(generics.GenericAPIView):
    serializer_class= None
    permission_classes = [IsRegistered]

    def delete(self, request, startupId, roundId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId, is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            round = InvestmentRound.objects.get(
                id=roundId,
                startup = startup,
                is_active= True
            )
            round.is_active = False
            round.save()
            return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except InvestmentRound.DoesNotExist:
            return Response({"error": "InvestmentRound does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EditInvestorinParticularRound(generics.GenericAPIView):
    serializer_class = CreateInvestorUserSerializer
    permission_classes = [IsRegistered]

    def put(self, request, startupId, investmentId, investorId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId, is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            round = InvestmentRound.objects.get(
                id=investmentId,
                startup = startup,
                is_active= True
            )
            investor = InvestorUser.objects.get(
                id=investorId,
                round = round
            )
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            investor.first_name = serializer.validated_data["firstName"]
            investor.last_name = serializer.validated_data["lastName"]
            investor.firm_name = serializer.validated_data["firmName"]
            investor.email = serializer.validated_data["email"]
            investor.amount_invested = serializer.validated_data["amountInvested"]
            investor.invested_type = serializer.validated_data["investedType"]
            investor.save()
            return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except InvestmentRound.DoesNotExist:
            return Response({"error": "InvestmentRound does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except InvestorUser.DoesNotExist:
            return Response({"error": "InvestorUser does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddInvestorinParticularRound(generics.GenericAPIView):
    serializer_class = CreateInvestorUserSerializer
    permission_classes = [IsRegistered]

    def post(self, request, startupId, investmentId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId, is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            round = InvestmentRound.objects.get(
                id=investmentId,
                startup = startup,
                is_active= True
            )
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            first_name = serializer.validated_data["firstName"]
            last_name = serializer.validated_data["lastName"]
            firm_name = serializer.validated_data["firmName"]
            email = serializer.validated_data["email"]
            amount_invested = serializer.validated_data["amountInvested"]
            invested_type = serializer.validated_data["investedType"]
            
            user_investment = InvestorUser.objects.create(
                round = round,
                first_name=first_name,
                last_name =last_name,
                firm_name = firm_name,
                email=email,
                amount_invested =amount_invested,
                invested_type = invested_type
                )
            url_in_request = reverse('investments-confirm', kwargs={'startupId': startupId, 'userInvestmentId': user_investment.id})
            accept_link = request.build_absolute_uri(url_in_request) + '?confirm=true'
            decline_link = request.build_absolute_uri(url_in_request) + '?confirm=false'
            utils.send_investors_invite_email(
                user_investment.email,
                startup.name,
                user_investment.first_name,
                user_investment.last_name,
                user_investment.firm_name,
                invested_type,
                amount_invested,
                round.amount,
                startup.industry_category.name,
                accept_link,
                decline_link
                )
            return Response(status=status.HTTP_201_CREATED)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except InvestmentRound.DoesNotExist:
            return Response({"error": "InvestmentRound does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class DeleteInvestorinParticularRound(generics.GenericAPIView):
    serializer_class = None
    permission_classes = [IsRegistered]

    def delete(self, request, startupId, investmentId, investorId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId, is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            round = InvestmentRound.objects.get(
                id=investmentId,
                startup=startup,
                is_active=True
            )
            investor = InvestorUser.objects.get(
                id=investorId,
                round=round
            )
            investor.is_active = False
            investor.save()
            
            return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except InvestmentRound.DoesNotExist:
            return Response({"error": "InvestmentRound does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except InvestorUser.DoesNotExist:
            return Response({"error": "InvestorUser does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EditParticularInvestmentRound(generics.GenericAPIView):
    serializer_class = EditInvestorinParticularRoundSerializer
    permission_classes = [IsRegistered]

    def put(self, request, startupId, investmentId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                serializer = self.get_serializer(data=request.data)
                round = InvestmentRound.objects.get(
                    id=investmentId,
                    startup = startup,
                    is_active= True
                )
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            round.round_type = serializer.validated_data["roundType"]
            round.amount = serializer.validated_data["amount"]
            round.raised_amount = serializer.validated_data["raisedAmount"]
            round.date = serializer.validated_data["date"]
            round.save()
            return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except InvestmentRound.DoesNotExist:
            return Response({"error": "InvestmentRound does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InversorTemporalPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': math.ceil(self.page.paginator.count / self.page_size), 
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

class InversorTemporalListView(generics.ListAPIView):
    permission_classes =  [IsRegistered]
    serializer_class = InversorTemporalSerializer
    pagination_class = InversorTemporalPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = InversorTemporalFilter
    
    def get_queryset(self):
        startup_id = self.kwargs['startupId']
        startup = Startup.objects.get(id=startup_id)
        stage = startup.stage
        final_query = InversorTemporal.objects.filter(
            industry_categories__in=StartupCategory.objects.filter(
                subcategories__industry__id=startup_id
                ),
            fund_stage__icontains=stage
            ).distinct()
        return final_query

    def get_serializer_context(self):
        context = super().get_serializer_context()
        startup_id = self.kwargs['startupId']
        
        favorite_investors = FavoriteInvestorsTemporal.objects.filter(startup_id=startup_id)
        favorite_investor_ids = list(favorite_investors.values_list('investor_id', flat=True))
        
        context['startupId'] = startup_id
        context['favorite_investor_ids'] = favorite_investor_ids
        return context
    
class FavoriteInvestorsListViews(generics.GenericAPIView):
    permission_classes = [IsRegistered]

    def get(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                favorites = FavoriteInvestorsTemporal.objects.filter(startup=startup)
                serializer = FavoriteInvestorsTemporalSerializer(favorites, many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class  FavoriteInvestorsViews(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    
    def post(self, request, startupId, investorId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                
                investor = InversorTemporal.objects.get(id=investorId)
                FavoriteInvestorsTemporal.objects.create(
                    startup = startup,
                    investor = investor
                )
            return Response(status=status.HTTP_201_CREATED)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except InversorTemporal.DoesNotExist:
            return Response({"error": "Investor does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, startupId, investorId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                
                favorite =FavoriteInvestorsTemporal.objects.get(
                    startup = startup,
                    investor_id = investorId
                )
                favorite.delete()
            return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except FavoriteInvestorsTemporal.DoesNotExist:
            return Response({"error": "Investor does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetEmailInvestorViews(generics.GenericAPIView):
    permission_classes = [IsRegistered]

    def get(self, request, startupId, investorId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                
                inversor =InversorTemporal.objects.get(id=investorId)
                url = f"mailto:{inversor.email}"
            return Response(data={"url":url},status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except InversorTemporal.DoesNotExist:
            return Response({"error": "Investor does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class InvestmentBanksView(generics.GenericAPIView):
    
    permission_classes = [IsRegistered]

    def get(self, request, startupId):
        try:
            date_180_days_ago = timezone.now().date() - timedelta(days=180)
            date_365_days_ago = timezone.now().date() - timedelta(days=365)
            user = self.request.user
            startup = Startup.objects.get(id=startupId, is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            
            country_list = ["Canada", "United States"]
            
            location_allowed = StartupLocation.objects.filter(
                startup=startup,
                country_name__in=country_list
            ).exists()
            
            
            if not location_allowed:
                ECL_labs_match = False
                stenn_match = False
            else:
                ECL_labs_match = StartupBusinessTraction.objects.filter(
                    startup=startup,
                    startup__foundation_date__lt=date_180_days_ago,
                    mrr__gte=8400,
                    business_revenue_sources=StartupBusinessTraction.B2B,
                ).exists()
                stenn_match = StartupBusinessTraction.objects.filter(
                    startup=startup,
                    startup__foundation_date__lt=date_365_days_ago,
                    mrr__gte=16000,
                    business_model__contains=StartupBusinessTraction.E_COMMERCE,
                    business_revenue_sources=StartupBusinessTraction.B2B,
                ).exists()
                    
            return Response(data={"ECLLabsMatch":ECL_labs_match, "stennMatch":stenn_match}, status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)