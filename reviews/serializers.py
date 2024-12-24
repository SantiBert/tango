from rest_framework import serializers

from django.conf import settings

from .models import Review

max_length_email = settings.MAX_LENGTH_CONFIG['email']
max_length_name = settings.MAX_LENGTH_CONFIG['names']
max_length_description = settings.MAX_LENGTH_CONFIG['description']

class ReviewListSerializer(serializers.ModelSerializer):
    overalRating = serializers.IntegerField(source='overal_rating')
    teamValue = serializers.IntegerField(source='team_value')
    problemValue = serializers.IntegerField(source='problem_value')
    solutionValue = serializers.IntegerField(source='solution_value')
    gtmstrategyValue = serializers.IntegerField(source='gtmstrategy_value')
    marketoppValue = serializers.IntegerField(source='marketopp_value')
    
    class Meta:
        model = Review
        fields = [
            'email',
            'overalRating', 
            'teamValue', 
            'problemValue',
            'solutionValue',
            'gtmstrategyValue',
            'marketoppValue',
            'details'
            ]
        
class CreateReviewSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=max_length_email, required=True)
    overalRating = serializers.IntegerField()
    teamValue = serializers.IntegerField()
    problemValue = serializers.IntegerField()
    solutionValue = serializers.IntegerField()
    gtmstrategyValue = serializers.IntegerField()
    marketoppValue = serializers.IntegerField()
    details = serializers.CharField(max_length=max_length_description, allow_blank=True)
    isAnonymous = serializers.BooleanField(default=True)