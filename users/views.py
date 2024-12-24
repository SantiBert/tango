import uuid
import re
import logging

from django.db import transaction
from django.contrib.auth import authenticate
from django.conf import settings

from rest_framework import status
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from pjbackend import utils

from startups.models import Founder
from payment.models import Subscription
from .models import CustomUser, Experience, PhoneNumberVerification
from .serializers import (
    ChangePasswordSerlializer,
    ForgotPasswordSerlializer,
    LoginSerializer,
    SignUpSerializer,
    ProfileUpdateFirstNameSerializer,
    ProfileUpdateLastNameSerializer,
    ProfileUpdateBioSerializer,
    ProfileUpdateSocialMediaSerializer, 
    ProfileUpdatetagLineSerializer, 
    ProfileSerializer,
    UserProfileCreateSerializer,
    UserProfileUpdateSerializer,
    ProfilePictureSerializer,
    ExperienceSerializer,
    VerificateCodeSerializer,
    )

from .permissions import IsRegistered

logger = logging.getLogger(__name__)

class VerificateSignupCodeView(generics.GenericAPIView):
    """
    Privateendpoint. Used to verificate a code
    to register a new user.
    """

    serializer_class = VerificateCodeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            code = serializer.data["code"]
            user_id = request.user.id
            code_ok = PhoneNumberVerification.verify(user_id, code)
            
            if not code_ok:
                return Response({"message": "Wrong code"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = CustomUser.objects.get(id=user_id)
            user.is_registered = True
            user.save()
            
            phone_verification = PhoneNumberVerification()
            phone_verification.remove_old_codes(user.id)
            
            is_onboarding = True
            startup = user.get_startup()
            if startup is not None:
                is_onboarding = False

            refresh = RefreshToken.for_user(user)
            
            data = {
                "token": str(refresh.access_token),
                "lifetime": utils.get_lifetime_token(),
                "refreshToken": str(refresh),
                "is_temporary_pass":user.is_temporary_pass,
                "isOnboarding":is_onboarding
            }
            return Response(data,status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"message": "Unexpected error", "detail": str(e)})
        
    def _generate_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            "token": str(refresh.access_token),
            "lifetime": utils.get_lifetime_token(),
            "refreshToken": str(refresh)
        }
        
class ResendVerificationCodeView(generics.GenericAPIView):
    """
    Private endpoint. Used to resend the verification code
    to register a new user.
    """
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        try:
            user = request.user
            phone_verification = PhoneNumberVerification()

            # Remove old verification codes for the user
            phone_verification.remove_old_codes(user.id)

            # Generate a new verification code for the user's phone number
            phone_verification.generate_for_register(user.phone_number, user.id)
            phone_verification.save()

            # Prepare and send SMS with the verification code
            message = f"Your PomJuice verification code is {phone_verification.verification_code}"
            utils.send_sms(str(user.phone_number), message)  # Ensure phone_number is cast to string

            return Response(status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            # Log the error for debugging purposes
            logger.error('Server error: %s', e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
             
class SignUpView(generics.CreateAPIView):
    """
    User register process
    Email and password required
    Return:
        -200: User created
        -400: Bad request, password or email in a wrong format
        -500: Some internal server error
    """
    permission_classes = ()
    authentication_classes = ()
    serializer_class = SignUpSerializer

    def post(self, request):
        user_serializer = SignUpSerializer(data=request.data)
        if not user_serializer.is_valid():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "Bad request", "errors": user_serializer.errors},
            )
        email = user_serializer.data["email"]
        password = user_serializer.data["password"]
        phone_number = user_serializer.data["phoneNumber"]
        is_terms_acepted = user_serializer.data["isTermsAcepted"]
        
        if not is_terms_acepted:
            return Response({"message": "terms not acepted"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                user = CustomUser.objects.filter(email=email).first()
                if user:
                    if user.is_active and user.is_registered:
                        return Response(
                            {"message": "Account already exists and is active"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    else:
                        user.is_registered = False
                        user.is_active = True
                        user.phone_number = phone_number
                else:
                    user = CustomUser.objects.create(
                        id=uuid.uuid4(),
                        email=email,
                        phone_number=phone_number,
                        is_terms_acepted=True
                    )
                    user.set_password(password)
                
                user.save()
                
                self._create_phone_verification(phone_number, user.id)
                self._founders_config(user)

                data = self._generate_tokens(user)
                
                return Response(data, status=status.HTTP_200_OK)

        except Exception as exp:
            logger.error('Server error: %s', exp)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"message": "Unexpected error", "detail": str(exp)})
    
    def _create_phone_verification(self, phone_number, user_id):
        phone_verification = PhoneNumberVerification()
        phone_verification.generate_for_register(phone_number, user_id)
        phone_verification.save()
        message = f"Your PomJuice verification code is {phone_verification.verification_code}"
        utils.send_sms(phone_number, message)


    def _generate_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            "token": str(refresh.access_token),
            "lifetime": utils.get_lifetime_token(),
            "refreshToken": str(refresh)
        }
    
    def _founders_config(self, user):
        founders = Founder.objects.filter(email=user.email, is_confirmed=True)
        for founder in founders:
            founder.user = user
            founder.save()
        

class LoginView(generics.GenericAPIView):
    permission_classes = ()
    authentication_classes = ()

    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            if not serializer.is_valid():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"message": "Bad request", "errors": serializer.errors},
                )
            
            email = serializer.data["email"]
            password = serializer.data["password"]
            is_onboarding = True
            user = authenticate(request, email=email, password=password)
            
            # Check if user exists but is not registered
            if user is not None and not user.is_registered:
                # Mask the phone number (e.g., +1234567890 -> +1****7890)
                phone_number = str(user.phone_number)
                masked_phone = f"{phone_number[:3]}{'*' * (len(phone_number) - 7)}{phone_number[-4:]}"
                
                # Resend verification code
                phone_verification = PhoneNumberVerification()
                phone_verification.remove_old_codes(user.id)
                phone_verification.generate_for_register(user.phone_number, user.id)
                phone_verification.save()
                
                message = f"Your PomJuice verification code is {phone_verification.verification_code}"
                utils.send_sms(str(user.phone_number), message)
                
                # Generate tokens for the unregistered user
                refresh = RefreshToken.for_user(user)
                data = {
                    "token": str(refresh.access_token),
                    "lifetime": utils.get_lifetime_token(),
                    "refreshToken": str(refresh),
                    "is_temporary_pass": user.is_temporary_pass,
                    "isOnboarding": True,
                    "needsVerification": True,
                    "maskedPhoneNumber": masked_phone
                }
                return Response(data, status=status.HTTP_200_OK)
            
            # Original authentication flow
            if user is None:
                return Response({"error": "Incorrect email or password"}, status=status.HTTP_401_UNAUTHORIZED)
            
            if not user.is_active:
                return Response({"error": "ncorrect email or password"}, status=status.HTTP_401_UNAUTHORIZED)
            
            startup = user.get_startup()
            if startup is not None:
                is_onboarding = False

            refresh = RefreshToken.for_user(user)
            
            data = {
                "token": str(refresh.access_token),
                "lifetime": utils.get_lifetime_token(),
                "refreshToken": str(refresh),
                "is_temporary_pass":user.is_temporary_pass,
                "isOnboarding":is_onboarding
            }
            response = Response(data, status=status.HTTP_200_OK)
            
            return response
        except CustomUser.DoesNotExist:
            return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DeleteAccountView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    
    def delete (self, request, *args, **kwargs):
        try:
            user = request.user
            startup = user.get_startup()
            if startup:
                subscription = Subscription.objects.filter(startup=startup).first()
                if subscription:
                    utils.cancel_stripe_subscription(subscription.stripe_subscription_id)
                    subscription.delete()
                startup.is_active = False
                startup.save()
                
            Experience.objects.filter(user =user).delete()
            
            user.phone_number = 'XXXXXXXXXXXXX'
            user.linkedin_url = ""
            user.first_name = ""
            user.last_name = ""
            user.x_url = None
            user.website_url = None
            user.calendly_url = None
            user.bio = None
            user.picture_url = None
            user.tag_line = None
            user.is_temporary_pass = False
            user.is_registered = False
            user.is_terms_acepted = False
            user.save()
            
            response = Response(status=status.HTTP_200_OK)
            
            return response
        except CustomUser.DoesNotExist:
            return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(generics.GenericAPIView):
    permission_classes = ()
    authentication_classes = ()
    
    serializer_class = ForgotPasswordSerlializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            if not serializer.is_valid():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"message": "Bad request", "errors": serializer.errors},
            )
            email = serializer.data["email"]
            
            user = CustomUser.objects.get(email=email)

            temp_password = utils.generate_temp_password()
            user.is_temporary_pass = True
            user.set_password(temp_password)
            user.save()
            utils.send_forgot_password_email(to_email=email, temp_password=temp_password, name= user.first_name)
            response = Response(status=status.HTTP_200_OK)
            
            return response
        except CustomUser.DoesNotExist:
            return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    serializer_class = ChangePasswordSerlializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            if not serializer.is_valid():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"message": "Bad request", "errors": serializer.errors},
            )
            user_id = request.user.id
            old_password = serializer.data["oldPassword"]
            new_password = serializer.data["newPassword"]

            user = CustomUser.objects.get(id=user_id)
            
            if not user.check_password(old_password):
                return Response(
                    {"error": "Incorrect Password"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            
            if user.is_temporary_pass:
                user.is_temporary_pass = False
            
            user.set_password(new_password)
            user.save()
            
            response = Response(status=status.HTTP_200_OK)
            
            return response
        except CustomUser.DoesNotExist:
            return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserEditFirstNameProfileView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    serializer_class = ProfileUpdateFirstNameSerializer

    def put(self, request):
        try:
            user = request.user
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            first_name = serializer.data["firstName"]
            validation = first_name.replace(" ", "")
            if not re.match(settings.REGEX_STRING, validation):
                return Response(
                    {"message": "the first name cannot have numbers or symbols"},
                    status=400,
                )
            user.first_name = first_name
            user.save()
            return Response({"message": "First Name changed"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserEditLastNameProfileView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    serializer_class = ProfileUpdateLastNameSerializer

    def put(self, request):
        try:
            user = request.user
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            last_name = serializer.data["lastName"]
            validation = last_name.replace(" ", "")
            if not re.match(settings.REGEX_STRING, validation):
                return Response(
                    {"message": "the last name cannot have numbers or symbols"},
                    status=400,
                )
            user.last_name = last_name
            user.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserEditBioProfileView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    serializer_class = ProfileUpdateBioSerializer

    def put(self, request):
        try:
            user = request.user
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            bio = serializer.data["bio"]
            user.bio = bio
            user.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserEditSocialMediaProfileView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    serializer_class = ProfileUpdateSocialMediaSerializer

    def put(self, request):
        try:
            user = request.user
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            social_media_data = serializer.validated_data
            user.linkedin_url = social_media_data.get("linkedinUrl", user.linkedin_url)
            user.x_url = social_media_data.get("xUrl", user.x_url)
            user.website_url = social_media_data.get("websiteUrl", user.website_url)
            user.calendly_url = social_media_data.get("calendlyUrl", user.calendly_url)
           
            user.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    serializer_class = UserProfileCreateSerializer
    
    def get(self, request):
        # Serializing the authenticated user's data
        try:
            serializer = ProfileSerializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        try:
          user = request.user
          user_serializer = UserProfileCreateSerializer(data=request.data)
          if not user_serializer.is_valid():
              return Response(
                  status=status.HTTP_400_BAD_REQUEST,
                  data={"message": "Bad request", "errors": user_serializer.errors},
                  )
          user_media_data = user_serializer.validated_data
          user.first_name = user_media_data.get("firstName",user.first_name)
          user.last_name = user_media_data.get("lastName",user.last_name)
          user.tag_line = user_media_data.get("tagLine",user.tag_line)
          user.save()
          utils.send_welcome_email(to_email=user.email, name= user.first_name)
          return Response({"userId": user.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  


class UpdateUserProfileView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    serializer_class = UserProfileUpdateSerializer
    
    def put(self, request):
        try:
          user = request.user
          user_serializer = self.get_serializer(data=request.data)
          if not user_serializer.is_valid():
              return Response(
                  status=status.HTTP_400_BAD_REQUEST,
                  data={"message": "Bad request", "errors": user_serializer.errors},
                  )
          user_media_data = user_serializer.validated_data
          user.first_name = user_media_data.get("firstName",user.first_name)
          user.last_name = user_media_data.get("lastName",user.last_name)
          user.bio = user_media_data.get("bio",user.bio)
          user.tag_line = user_media_data.get("tagLine",user.tag_line)
          user.linkedin_url = user_media_data.get("linkedinUrl",user.linkedin_url)
          user.x_url = user_media_data.get("xUrl",user.x_url)
          user.website_url = user_media_data.get("websiteUrl",user.website_url)
          user.calendly_url = user_media_data.get("calendlyUrl",user.calendly_url)
                
          image = user_media_data.get("image")
          if image:
              file_url = utils.upload_file_to_s3(image)
              user.picture_url = file_url
    
          user.save()
          
          experiences = user_media_data.get("experiences", [])
          
          if len(experiences) > 0:
              Experience.objects.filter(user=user).delete()
              for experience_data in experiences:
                  Experience.objects.create(
                        user=user,
                        title=experience_data['title'],
                        company=experience_data['company'],
                        start_date=experience_data['startDate'],
                        end_date=experience_data['endDate']
                    )
          
          return Response({"userId": user.id}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserEditTagLineProfileView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    serializer_class = ProfileUpdatetagLineSerializer

    def put(self, request):
        try:
            user = request.user
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            tag_line = serializer.data["tagLine"]
            user.tag_line = tag_line
            user.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
class UserProfileProfessionalHistoryView(generics.GenericAPIView):
    permission_classes = [IsRegistered]

    def get_serializer_class(self):
        # This method ensures the right serializer is used for each HTTP method. pomjuice-environment 	pmjuice
        return ExperienceSerializer

    def get(self, request):
        # Handles GET requests to retrieve the user's professional history.
        experiences = Experience.objects.filter(user=request.user)
        serializer = self.get_serializer(experiences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Handles POST requests to update the user's professional history.
        user = request.user
        
        
        serializer = self.get_serializer(data=request.data['listOfExperiences'], many=True)
        if serializer.is_valid():
            with transaction.atomic():
                # Deleting the user's current experiences
                Experience.objects.filter(user=user).delete()

                # Create new experiences based on the validated data
                new_experiences = [Experience(user=user, **data) for data in serializer.validated_data]
                Experience.objects.bulk_create(new_experiences)

                return_serializer = self.get_serializer(new_experiences, many=True)
                return Response(return_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class UserProfilePictureView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    serializer_class = ProfilePictureSerializer
    
    def put(self, request):
        try:
            user = request.user
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            image = serializer.validated_data.get("image")
            file_url = utils.upload_file_to_s3(image)
            user.picture_url = file_url
            user.save()
            
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
