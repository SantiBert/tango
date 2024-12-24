import logging

from rest_framework import generics, status
from rest_framework.response import Response

from .models import Review

from .serializers import ReviewListSerializer, CreateReviewSerializer

from startups.models import Startup

from users.permissions import IsRegistered

logger = logging.getLogger(__name__)

class ReviewListView(generics.GenericAPIView):
    serializer_class = ReviewListSerializer
    permission_classes = [IsRegistered]

    def get(self, request, startupId):
        try:
            user = self.request.user
            startup = Startup.objects.get(id=startupId, main_founder=user,is_active=True)
            if not startup.user_has_access(user):
                return Response({"error": "You don't have access"}, status=status.HTTP_404_NOT_FOUND)
            review_list = Review.objects.filter(startup=startup, is_active=True)
            serializer = ReviewListSerializer(review_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class CreateReviewView(generics.GenericAPIView):
    serializer_class = CreateReviewSerializer
    permission_classes = ()
    
    def post(self, request, startupId):
        try:
            startup = Startup.objects.get(id=startupId, is_active=True)
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            email= serializer.validated_data["email"]
            if Review.objects.filter(email=email,startup=startup).exists():
                return Response({"error": "You have already sent your review of this startup"}, status=status.HTTP_400_BAD_REQUEST)
            
            startup = Review.objects.create(
                email = email,
                startup = startup,
                overal_rating = serializer.validated_data["overalRating"],
                team_value = serializer.validated_data["teamValue"],
                problem_value = serializer.validated_data["problemValue"],
                solution_value = serializer.validated_data["solutionValue"],
                gtmstrategy_value = serializer.validated_data["gtmstrategyValue"],
                marketopp_value = serializer.validated_data["marketoppValue"],
                details = serializer.validated_data["details"],
                is_anonymous = serializer.validated_data["isAnonymous"],
            )
            return Response(status=status.HTTP_201_CREATED)
        except Startup.DoesNotExist:
            return Response({"error": "Startup does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    