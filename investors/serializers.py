from rest_framework import serializers

from django.conf import settings

from .models import (
    InvestmentRound, 
    InvestorUser, 
    InversorTemporal, 
    FavoriteInvestorsTemporal
)

max_length_name = settings.MAX_LENGTH_CONFIG['names']
max_length_email = settings.MAX_LENGTH_CONFIG['email']
max_length_description = settings.MAX_LENGTH_CONFIG['description']

class InvestorUserSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    firmName = serializers.CharField(source='firm_name')
    amountInvested = serializers.IntegerField(source='amount_invested')
    investedType = serializers.CharField(source='invested_type')
    isVerificated = serializers.CharField(source='is_verificated')
  
    class Meta:
        model = InvestorUser
        fields = [
            'id',
            'firstName',
            'lastName',
            'email',
            'firmName',
            'amountInvested',
            'investedType',
            'isVerificated',

            ]

class InvestmentRoundSerializer(serializers.ModelSerializer):
    roundType = serializers.CharField(source='round_type')
    roundId = serializers.IntegerField(source='id')
    raisedAmount = serializers.IntegerField(source='raised_amount')
    investors = serializers.SerializerMethodField(method_name="get_investors")
    
    def get_investors(self, obj):
        investor = InvestorUser.objects.filter(
            round=obj, 
            is_active=True, 
            is_verificated__in=[InvestorUser.VERIFIED, InvestorUser.PENDING]           
            )
        if investor.exists():
            investors_serializer =InvestorUserSerializer(investor,many=True)
            return investors_serializer.data
        else:
            return []
    
    class Meta:
        model = InvestmentRound
        fields = [
            'roundId',
            'roundType',
            'investors',
            'amount',
            'raisedAmount',
            'date',            
            ]

class CreateInvestorUserSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=max_length_name, required=True)
    lastName = serializers.CharField(max_length=max_length_name, required=True)
    email = serializers.EmailField(max_length=max_length_email, required=True)
    firmName = serializers.CharField(max_length=max_length_name, required=True)
    amountInvested = serializers.IntegerField(required=True)
    investedType = serializers.CharField(max_length=max_length_name, required=True)

class CreateInvestmentRoundSerializer(serializers.Serializer):
    roundType = serializers.CharField(max_length=max_length_name, required=True)
    amount = serializers.IntegerField(required=True)
    raisedAmount = serializers.IntegerField(required=True)
    date = serializers.DateTimeField(required=False)
    investors = CreateInvestorUserSerializer(many=True, required=True)



class InvestmentRoundChangeAmountSerializer(serializers.Serializer):
    amount = serializers.IntegerField(required=True)
    
class InvestmentRoundChangeRaisedAmountSerializer(serializers.Serializer):
    raisedAmount = serializers.IntegerField(required=True)

class EditInvestorinParticularRoundSerializer(serializers.Serializer):
    roundType = serializers.CharField(max_length=max_length_name, required=True)
    amount = serializers.IntegerField(required=True)
    raisedAmount = serializers.IntegerField(required=True)
    date = serializers.DateTimeField(required=False)

class InversorTemporalSerializer(serializers.ModelSerializer):
    isSaved =  serializers.SerializerMethodField(method_name="get_isSaved")
    industry = serializers.SerializerMethodField(method_name="get_industry")
    
    def get_isSaved(self, obj):
        favorite_investor_ids = self.context.get('favorite_investor_ids', [])
        return obj.id in favorite_investor_ids
    
    def get_industry(self, obj):
        industry_categories = obj.industry_categories.all()
        
        if industry_categories:
            names = industry_categories.values_list('name', flat=True)
            categorias_string = ', '.join(names)
            return categorias_string
        else:
            return None
    
    class Meta:
        model = InversorTemporal
        fields = [
            'id',
            'first_name', 
            'last_name', 
            'firm_name', 
            'website', 
            'founding_year', 
            'description', 
            'fund_stage', 
            'fund_type', 
            'linkedin_link', 
            'twitter_link', 
            'city', 
            'state', 
            'country', 
            'location', 
            'industry', 
            'status', 
            'test',
            'isSaved'
        ]

class InversorTemporalListSerializer(serializers.ModelSerializer):
    industry = serializers.SerializerMethodField(method_name="get_industry")
    
    def get_industry(self, obj):
        industry_categories = obj.industry_categories.all()
        
        if industry_categories:
            names = industry_categories.values_list('name', flat=True)
            categorias_string = ', '.join(names)
            return categorias_string
        else:
            return None
  
    class Meta:
        model = InversorTemporal
        fields = [
            'id',
            'first_name', 
            'last_name', 
            'firm_name', 
            'website', 
            'founding_year', 
            'description', 
            'fund_stage', 
            'fund_type', 
            'linkedin_link', 
            'twitter_link', 
            'city', 
            'state', 
            'country', 
            'location', 
            'industry', 
            'status', 
            'test',
        ]
        
class FavoriteInvestorsTemporalSerializer(serializers.ModelSerializer):
    investor = InversorTemporalListSerializer(read_only=True)

    class Meta:
        model = FavoriteInvestorsTemporal
        fields = ['investor']