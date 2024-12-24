import logging

from django.db import transaction
from django.urls import reverse
from django.http import HttpResponse
from dotenv import load_dotenv
from rest_framework import generics, status
from rest_framework.response import Response

from pjbackend import utils
from .models import (
    Startup, 
    StartupSubcategory,
    Founder, 
    StartupImage,
    StartupVideo,
    StartupLocation,
    StartupBusinessTraction,
    StartupTopCustomer,
    StartupSlidedeck,
    StartupShare,
    StartupTechSector,
    PublicVisitor,
    PrivateVisitor
)
from payment.models import Subscription
from .serializers import (
    DetailedOutsiderStartupViewerSerializer,
    StartupSerializer,
    StartupTechSectorSerializer,
    StartupSubcategorySerializer,
    CreateStartupSerializer,
    CreateStartupShareSerializer,
    CreateVisitorSerializer,
    CreatePrivateVisitorSerializer,
    EditStartupIndustrySerializer,
    EditStartupLocationSerializer,
    EditStartupNameSerializer,
    EditStartupSerializer,
    EditStartupStageSerializer,
    EditStartupWebsiteSerializer,
    EditStartupFoundationDateSerializer,
    EditPrivacySerializer,
    FounderSerializer,
    FounderConfirmSerializer,
    FounderCreateSerializer,
    FounderEditSerializer,
    StartupCreatePitchDeckSerializer,
    EditStartupImageSerializer,
    EditStartupVideoSerializer, 
    EditStartupDescriptionSerializer,
    StartupBusinessTractionSerializer,
    StartupBusinessTractionCreateSerializer,
    StartupBusinessTractionEditSerializer
)

from users.permissions import IsRegistered
from users.models import CustomUser

logger = logging.getLogger(__name__)
load_dotenv()

class StartupCategoryView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    
    def get(self, request):
        try:
            categories = StartupSubcategory.objects.all()
            serializer = StartupSubcategorySerializer(categories, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StartupCategoryTechSectorView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    
    def get(self, request):
        try:
            categories = StartupTechSector.objects.all()
            serializer = StartupTechSectorSerializer(categories, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StartupView(generics.GenericAPIView):
    serializer_class = CreateStartupSerializer
    permission_classes = [IsRegistered]

    def get(self, request):
        user = request.user
        try:
            startup = user.get_startup()
            if not startup:
                return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
            serializer = StartupSerializer(startup)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        try:
            user = request.user
            user_is_main_founder = Startup.objects.filter(main_founder=user,is_active=True).exists()
            user_is_co_founder = Startup.objects.filter(founders__user=user, founders__is_confirmed=True, is_active=True).exists()
            if user_is_main_founder or user_is_co_founder:
                return Response({"error": "You already have a Startup created, you cannot have more than one"}, status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            founder_data = serializer.validated_data
            startup = Startup.create_startup(
                name = serializer.validated_data["name"],
                main_founder = request.user,
                industry_category_id = serializer.validated_data["industry"],
                tech_sector_id =  serializer.validated_data["techSector"],
                location = serializer.validated_data["location"],
                employee_count = serializer.validated_data["employeeCount"],
                foundation_date = serializer.validated_data["foundationDate"],
                stage = founder_data.get("stage", None),
                website_url = founder_data.get("websiteUrl", None),                
            )
            utils.send_email(subject="startup created", to_email=user.email,content=f"startup created - startup:{startup.name}")
            return Response({"startupId": startup.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
        

class StarupDetailView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    
    def get(self, request, startupId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId,is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            serializer = StartupSerializer(startup)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StartupPublicView(generics.GenericAPIView):
    serializer_class = CreateVisitorSerializer
    permission_classes = ()
    
    def post(self, request, startupId):
        try:
            with transaction.atomic():
                device_id = request.META.get('HTTP_X_DEVICE_ID')
                if not device_id:
                    return Response({"error": "Device id not found"}, status=status.HTTP_400_BAD_REQUEST)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                
                if not serializer.validated_data["isTermsAcepted"]:
                    return Response({"error": "Terms and conditions must be accepted"}, status=status.HTTP_400_BAD_REQUEST)
                startup = Startup.objects.get(id=startupId,is_active=True, is_public=True)
                startup_serializer = DetailedOutsiderStartupViewerSerializer(startup)
                email =  serializer.validated_data["email"]
                if PublicVisitor.objects.filter(email=email,startup=startup).exists():
                    return Response(startup_serializer.data, status=status.HTTP_200_OK)
                else:
                    PublicVisitor.objects.create(
                        email = email,
                        startup=startup,
                        device_id = device_id,
                        is_terms_acepted = True
                    )              
                    return Response(data=startup_serializer.data, status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StartupEditStage(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    serializer_class = EditStartupStageSerializer
     
    def put(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                startup.stage = serializer.validated_data["stage"]
                startup.save()
                return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StartupEditName(generics.GenericAPIView):
    serializer_class = EditStartupNameSerializer
    permission_classes = [IsRegistered]
    
    def put(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                startup.name = serializer.validated_data["name"]
                startup.save()
                return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error: Startup does not exist"}, status = status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class StartupEditLocation(generics.GenericAPIView):
    serializer_class = EditStartupLocationSerializer
    permission_classes = [IsRegistered]
    
    def put(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                
                location = serializer.validated_data["location"]
                startup_location = StartupLocation.objects.get(startup_id=startupId)
                city, state, country = location.split(", ")
                startup_location.full_name = location
                startup_location.city_name = city
                startup_location.state_name = state
                startup_location.country_name = country
                startup_location.save()
            return Response("Location updated successfully",status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error: Startup does not exist"}, status = status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StartupEditIndustry(generics.GenericAPIView):
    serializer_class = EditStartupIndustrySerializer
    permission_classes = [IsRegistered]

    def put(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                startup.industry_category_id = serializer.validated_data["industry"]
                startup.save()
                return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error: Startup does not exist"}, status = status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    

class StartupEditView(generics.GenericAPIView):
    serializer_class = EditStartupSerializer
    permission_classes = [IsRegistered]

    def put(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                
                founder_data = serializer.validated_data
                startup.name = founder_data.get("name",startup.name)
                startup.employee_count = founder_data.get("employeeCount",startup.employee_count)
                startup.stage = founder_data.get("stage",startup.stage)
                startup.website_url = founder_data.get("websiteUrl",startup.website_url)
                startup.foundation_date = founder_data.get("foundationDate",startup.foundation_date)
                startup.industry_category_id  = founder_data.get("industry",startup.industry_category_id)
                startup.tech_sector_id  = founder_data.get("techSector",startup.tech_sector_id)
                startup.save()
                
                location = founder_data.get("location", None)
                
                if location:
                    startup_location = StartupLocation.objects.get(startup_id=startupId)
                    city, state, country = location.split(", ")
                    startup_location.full_name = location
                    startup_location.city_name = city
                    startup_location.state_name = state
                    startup_location.country_name = country
                    startup_location.save()
                
            return Response({"startupId": startup.id}, status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
        
class StartupEditWebsite(generics.GenericAPIView):
    serializer_class = EditStartupWebsiteSerializer
    permission_classes = [IsRegistered]

    def put(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                serializer = self.get_serializer(data = request.data)
                if not serializer.is_valid():
                    return Response({"error": serializer.errors}, status = status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                startup.website_url = serializer.validated_data["websiteUrl"]
                startup.save()
                return Response(status = status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error":"Startup Does not Exist"}, status = status.HTTP_404_NOT_FOUND )
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status= status.HTTP_500_INTERNAL_SERVER_ERROR)

class FoundersView(generics.GenericAPIView):
    serializer_class = FounderCreateSerializer
    permission_classes = [IsRegistered]
    
    def get(self, request, startupId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId, is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            founders = Founder.objects.filter(startup=startup)
            serializer = FounderSerializer(founders,many=True)
            data = serializer.data
            data.append({
                'firstName':startup.main_founder.first_name,
                'lastName':startup.main_founder.last_name,
                'pictureUrl':startup.main_founder.picture_url,
                })
            return Response(data, status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, main_founder=user, is_active=True)
                serializer = self.get_serializer(data=request.data, many=True)
                
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                for founder_data in serializer.validated_data:
                    first_name = founder_data.get('firstName')
                    last_name = founder_data.get('lastName')
                    email = founder_data.get('email')
                    role = founder_data.get('role', None)
                    
                    user_is_co_founder = Founder.objects.filter(email=email, is_confirmed=True).exists()
                    
                    if not user_is_co_founder:

                        user_already_invited = Founder.objects.filter(startup=startup, email=email)
                        
                        if user_already_invited.exists():
                            possible_founder = user_already_invited.first()
                            
                            if not possible_founder.is_confirmed:
                                invite_link_in_request = reverse('founder-confirm', kwargs={'startupId': startupId, 'founderId': possible_founder.id})
                                invite_link = request.build_absolute_uri(invite_link_in_request) + '?confirm=true'
                                utils.send_cofounder_invite_email(
                                    to_email=email,
                                    name=possible_founder.first_name,
                                    company_name=startup.name,
                                    invite_link=invite_link
                                )
                        else:
                            founder = Founder.objects.create(
                                startup=startup,
                                first_name=first_name,
                                last_name=last_name,
                                role=role,
                                email=email,
                            )
                            invite_link_in_request = reverse('founder-confirm', kwargs={'startupId': startupId, 'founderId': founder.id})
                            invite_link = request.build_absolute_uri(invite_link_in_request) + '?confirm=true'
                            utils.send_cofounder_invite_email(
                                to_email=email,
                                name=first_name,
                                company_name=startup.name,
                                invite_link=invite_link
                            )
                
                return Response(status=status.HTTP_201_CREATED)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FounderConfirmView(generics.GenericAPIView):
    serializer_class = FounderConfirmSerializer
    permission_classes = ()
    
    def post(self, request, startupId, founderId):
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            startup = Startup.objects.get(id=startupId,is_active=True)
            founder = Founder.objects.get(id=founderId,startup=startup)
            
            user_is_co_founder = Founder.objects.filter(user=founder.user, is_confirmed=True).exists()
            
            if founder.is_confirmed:
                return Response({"error":"has already been confirmed"}, status=status.HTTP_400_BAD_REQUEST)
            
            if user_is_co_founder:
                return Response(
                    {"error":"You already have a Startup created, you cannot have more than one"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            founder_data = serializer.validated_data["confirm"]
            founder.is_confirmed = founder_data
            
            users = CustomUser.objects.filter(email=founder.email)
            
            if users.exists():
                founder.user = users[0]
            
            founder.save()

            return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Founder.DoesNotExist:
            return Response({"error": "Founder does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request, startupId, founderId):
        try:
            confirm = request.query_params.get('confirm', 'false') == 'true'
            
            startup = Startup.objects.get(id=startupId, is_active=True)
            founder = Founder.objects.get(id=founderId, startup=startup)
            
            user_is_co_founder = Founder.objects.filter(email=founder.email, is_confirmed=True).exists()
            
            if founder.is_confirmed:
                return HttpResponse("<h1>Error</h1><p>Has already been confirmed.</p>", status=status.HTTP_400_BAD_REQUEST)
        
            if user_is_co_founder:
                return HttpResponse("<h1>Error</h1><p>You already have a Startup created, you cannot have more than one.</p>", status=status.HTTP_400_BAD_REQUEST)
                
            founder.is_confirmed = confirm
            
            users = CustomUser.objects.filter(email=founder.email)
            
            if users.exists():
                founder.user = users[0]
            
            founder.save()
            success_message = f"<h1>Success</h1><p>Now you are a co-founder of {startup.name}.</p>"
            return HttpResponse(success_message, status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return HttpResponse("<h1>Error</h1><p>Startup does not exist.</p>", status=status.HTTP_404_NOT_FOUND)
        except Founder.DoesNotExist:
            return HttpResponse("<h1>Error</h1><p>Founder does not exist.</p>", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return HttpResponse(f"<h1>Error</h1><p>Server error: {str(e)}</p>", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FounderEditView(generics.GenericAPIView):
    serializer_class = FounderEditSerializer
    permission_classes = [IsRegistered]
    
    def put(self, request, startupId, founderId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId, is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            founder = Founder.objects.get(id=founderId,startup=startup)
            
            serializer = self.get_serializer(data=request.data, context={'founder': founder})
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                
            founder_data = serializer.validated_data
            
            new_email = founder_data["email"]
            
            if new_email != founder.email:
                user_is_co_founder = Founder.objects.filter(email=new_email, is_confirmed=True).exists()
                if not user_is_co_founder:
                    first_name = founder_data.get("firstName",founder.first_name)
                    invite_link_in_request = reverse('founder-confirm', kwargs={'startupId': startupId, 'founderId': founder.id})
                    invite_link = request.build_absolute_uri(invite_link_in_request) + '?confirm=true'
                    utils.send_cofounder_invite_email(
                        to_email=new_email,
                        name=first_name,
                        company_name=startup.name,
                        invite_link=invite_link
                        )
                    founder.email = new_email
            
            founder.first_name = founder_data.get("firstName",founder.first_name)
            founder.last_name = founder_data.get("lastName",founder.last_name)
            founder.role = founder_data.get("role",founder.role)            
            founder.save()

            return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Founder.DoesNotExist:
            return Response({"error": "Founder does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FounderDeleteView(generics.GenericAPIView):
    serializer_class = None
    permission_classes = [IsRegistered]
    
    def delete(self, request, startupId, founderId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId, is_active=True)
            founder = Founder.objects.get(id=founderId,startup=startup)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            if founder.user:
                if founder.user_id == user.id:
                    return Response({"error": "You can't delete the main founder"}, status=status.HTTP_400_BAD_REQUEST)
            
            founder.delete()
            
            return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Founder.DoesNotExist:
            return Response({"error": "Founder does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       
class StartupImageEdit(generics.GenericAPIView):
    serializer_class = EditStartupImageSerializer
    permission_classes = [IsRegistered]
    
    def put(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                startup = Startup.objects.get(id=startupId, is_active=True) 
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                image = serializer.validated_data.get("image")
                if not image:
                    logger.error("Image File not provided in the request")
                    return Response({"error": "Image File not provided"}, status=status.HTTP_400_BAD_REQUEST)
                file_url = utils.upload_file_to_s3(image)
                if not file_url:
                    logging.error("Failed to upload image to S3")
                    return Response({"error": "Failed to upload image to S3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                StartupImage.objects.filter(startup=startup, is_active=True).update(is_active=False)
                StartupImage.objects.create( 
                    startup=startup,
                    url=file_url,
                    is_active=True
                )
                return Response({"message": "Startup image updated successfully"}, status=status.HTTP_200_OK)
        
        except Startup.DoesNotExist:
            return Response({"error": "Startup not found"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logging.error('Unexpected error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)     
                                        
class StartupPrivacyView(generics.GenericAPIView):
    serializer_class = EditPrivacySerializer
    permission_classes = [IsRegistered]
    
    def put(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                startup.is_public = serializer.validated_data["isPrivacy"]
                startup.save()
                return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StartupEditVideo(generics.GenericAPIView):
    serializer_class = EditStartupVideoSerializer
    permission_classes = [IsRegistered]

    def put(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                video = serializer.validated_data.get("video")
                if not video:
                    logger.error("Video not provided in the request")
                    return Response({"error": "Video not provided"}, status=status.HTTP_400_BAD_REQUEST)
               
                file_url = utils.upload_file_to_s3(video)
                if not file_url:
                    logging.error("Failed to upload image to S3")
                    return Response({"error": "Failed to upload Video to S3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                StartupVideo.objects.filter(startup=startup, is_active = True).update(is_active=False)  
                StartupVideo.objects.create(
                    startup=startup,
                    url=file_url,
                    is_active=True
                )
                return Response({"message": "Startup Video updated successfully"}, status=status.HTTP_200_OK)
            
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                video = StartupVideo.objects.filter(startup=startup, is_active = True).first()
                if not video:
                    return Response({"error": "Startup does not have video"}, status=status.HTTP_400_BAD_REQUEST)
                video.is_active = False
                video.save()     
                return Response({"message": "Startup Video deleted successfully"}, status=status.HTTP_200_OK)
            
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StartupEditDescription(generics.GenericAPIView):
    serializer_class = EditStartupDescriptionSerializer
    permission_classes = [IsRegistered]

    def put(self,request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                startup.description = serializer.validated_data["description"]
                startup.save()
                return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error: Startup does not exist"}, status = status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StartupEditFoundationDate(generics.GenericAPIView):
    serializer_class = EditStartupFoundationDateSerializer
    permission_classes = [IsRegistered]

    def put(self,request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                startup.foundation_date = serializer.validated_data["foundationDate"]
                startup.save()
                return Response(status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error: Startup does not exist"}, status = status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StartupEditPitchDeckUpload(generics.GenericAPIView):
    serializer_class = StartupCreatePitchDeckSerializer  
    permission_classes = [IsRegistered]

    def put(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                pitchDeck = serializer.validated_data.get("pitchDeck")

                if not pitchDeck:
                    return Response({"error": "Pitch Deck File not provided"}, status=status.HTTP_400_BAD_REQUEST)
                
                file_url = utils.upload_file_to_s3(pitchDeck)
                if not file_url:
                    logging.error("Failed to upload image to S3")
                    return Response({"error": "Failed to upload pitchDeck to S3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                StartupSlidedeck.objects.filter(startup=startup,is_active= True).update(is_active=False)
                StartupSlidedeck.objects.create(
                    startup=startup,
                    url=file_url,
                    is_active=True
                )
                return Response({"message": "Startup Pitch Deck updated successfully"}, status=status.HTTP_200_OK)

        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logging.error('Unexpected error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
                     
           
class BusinessTractionView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    
    def get(self, request, startupId):
        try:
            user = request.user
            startup = Startup.objects.get(id=startupId, is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            business_traction = StartupBusinessTraction.objects.get(startup=startup)
            serializer = StartupBusinessTractionSerializer(business_traction)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except StartupBusinessTraction.DoesNotExist:
            return Response({"error": "Business Traction does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request,startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId,is_active=True)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                if StartupBusinessTraction.objects.filter(startup=startup).exists():
                    return Response({"error": "You already have a Business Traction created, you cannot have more than one"}, status=status.HTTP_400_BAD_REQUEST)
                
                serializer = StartupBusinessTractionCreateSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                
                business_model = serializer.validated_data["businessModel"]
                business_revenue_sources = serializer.validated_data["businessRevenueSources"]
                mrr = serializer.validated_data["mrr"]
                top_customers = serializer.validated_data["topCustomers"]
                
                business_traction = StartupBusinessTraction.objects.create(
                    startup = startup,
                    business_revenue_sources = business_revenue_sources,
                    mrr=mrr
                )
                business_traction.set_business_model_list(business_model)
                business_traction.save()
                
                for top_customer in top_customers:
                    name = top_customer.get('name')
                    url = top_customer.get('url')
                    StartupTopCustomer.objects.create(
                        startup = startup,
                        business_traction=business_traction,
                        name =name,
                        url = url
                    )
            return Response(status=status.HTTP_201_CREATED)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId, is_active=True)
                business_traction = StartupBusinessTraction.objects.get(startup=startup)
                serializer = StartupBusinessTractionEditSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                if not startup.user_has_access(user):
                    return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
                business_traction = startup.business_tractions
                business_tractions_data = serializer.validated_data
                business_model = business_tractions_data.get("businessModel",business_traction.business_model)
                business_traction.business_revenue_sources = business_tractions_data.get("businessRevenueSources",business_traction.business_revenue_sources)
                business_traction.mrr = business_tractions_data.get("mrr",business_traction.mrr)
                business_traction.set_business_model_list(business_model)
                business_traction.save()
                
                top_customers = business_tractions_data.get("topCustomers")

                if top_customers and len(top_customers) > 0:
                    StartupTopCustomer.objects.filter(startup=startup,business_traction=business_traction).delete()
                    for top_customer in top_customers:
                        name = top_customer.get('name')
                        url = top_customer.get('url')
                        StartupTopCustomer.objects.create(
                            startup = startup,
                            business_traction=business_traction,
                            name =name,
                            url = url
                        )
                business_traction.save()       
            return Response({"startupId": startup.id}, status=status.HTTP_200_OK)
        except StartupBusinessTraction.DoesNotExist:
            return Response({"error": "Business Traction does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class StartupShareView(generics.GenericAPIView):
    serializer_class = CreateStartupShareSerializer
    permission_classes = [IsRegistered]
    
    def post(self, request,startupId):
        try:
            with transaction.atomic():
                user = request.user
                startup = Startup.objects.get(id=startupId,is_active=True)
                founders = Founder.objects.filter(startup_id =startupId)
                founder_ids = [founder.id for founder in founders]
                founder_ids.append(startup.main_founder.id)
                if user.id not in founder_ids:
                    return Response({"error": "You don't have access"}, status=status.HTTP_400_BAD_REQUEST)
                
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                
                if StartupShare.objects.filter(startup=startup,email=serializer.validated_data["email"]).exists():
                    return Response({"error": "You have already shared to this email"}, status=status.HTTP_400_BAD_REQUEST)
                if Subscription.objects.filter(startup = startup).count()> 4:
                    return Response({"error": "You have reached the maximum number of shares"}, status=status.HTTP_400_BAD_REQUEST)
                StartupShare.objects.create(
                    startup = startup,
                    first_name=serializer.validated_data["firstName"],
                    last_name =serializer.validated_data["lastName"],
                    email = serializer.validated_data["email"],
                    relationship = serializer.validated_data["relationship"]
                    )
                if not startup.is_public:
                    visitor = PrivateVisitor.objects.create(
                        email = serializer.validated_data["email"],
                        startup = startup
                    )
                    print(f"email:{visitor.email}, token:{visitor.unique_token}, {startup.id}")
                #TODO Create endpoint to see other startups
            return Response(status=status.HTTP_201_CREATED)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class CheckoutPublicVisitorView(generics.GenericAPIView):
    permission_classes = ()
    
    def get(self, request, startupId):
        try:
            device_id = request.META.get('HTTP_X_DEVICE_ID')
            if not device_id:
                return Response({"error": "Device id not found"}, status=status.HTTP_400_BAD_REQUEST)
            startup = Startup.objects.get(id=startupId, is_active=True, is_public=True)
            
            if PublicVisitor.objects.filter(device_id=device_id, startup=startup).exists():
                serializer = DetailedOutsiderStartupViewerSerializer(startup)
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(data={"new_visitor": True}, status=status.HTTP_200_OK)
            
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckoutPrivateVisitorView(generics.GenericAPIView):
    permission_classes = ()
    
    def get(self, request, startupId,email, token):
        try:
            device_id = request.META.get('HTTP_X_DEVICE_ID')
            if not device_id:
                return Response({"error": "Device id not found"}, status=status.HTTP_400_BAD_REQUEST)
            startup = Startup.objects.get(id=startupId, is_active=True, is_public=False)
            if PrivateVisitor.objects.filter(device_id=device_id,email=email,unique_token=token,startup=startup).exists():
                serializer = DetailedOutsiderStartupViewerSerializer(startup)
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(data={"new_visitor": True}, status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class StartupPrivateView(generics.GenericAPIView):
    serializer_class = CreatePrivateVisitorSerializer
    permission_classes = ()
    
    def post(self, request, startupId, email, token):
        try:
            with transaction.atomic():
                device_id = request.META.get('HTTP_X_DEVICE_ID')
                if not device_id:
                    return Response({"error": "Device id not found"}, status=status.HTTP_400_BAD_REQUEST)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                
                if not serializer.validated_data["isTermsAcepted"]:
                    return Response({"error": "Terms and conditions must be accepted"}, status=status.HTTP_400_BAD_REQUEST)
                startup = Startup.objects.get(id=startupId,is_active=True, is_public=False)
                startup_serializer = DetailedOutsiderStartupViewerSerializer(startup)
                
                visitor = PrivateVisitor.objects.get(
                    email = email,
                    unique_token = token,
                    startup_id = startupId
                )
                
                visitor.device_id = device_id
                visitor.is_terms_acepted = serializer.validated_data["isTermsAcepted"]
                visitor.save()
                
                return Response(data=startup_serializer.data, status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except PrivateVisitor.DoesNotExist:
            return Response({"error": "PrivateVisitor does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
