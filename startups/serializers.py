import re
from rest_framework import serializers

from django.conf import settings

from investors.serializers import InvestmentRoundSerializer

from .models import (
    StartupCategory,
    StartupSubcategory,
    StartupTechSector,
    Startup,
    StartupVideo,
    StartupImage,
    StartupLocation,
    StartupSlidedeck,
    StartupBusinessTraction,
    StartupTopCustomer,
    Founder
    )
from users.serializers import ProfileSerializer, SmallUserSerializer

from investors.models import InvestmentRound
from payment.models import Subscription

max_length_name = settings.MAX_LENGTH_CONFIG['names']
max_length_email = settings.MAX_LENGTH_CONFIG['email']
max_length_description = settings.MAX_LENGTH_CONFIG['description']
max_length_industry = settings.MAX_LENGTH_CONFIG['industry']
max_length_location = settings.MAX_LENGTH_CONFIG['location']
max_length_url = settings.MAX_LENGTH_CONFIG['url']

class StartupVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupVideo
        fields = ['url']

class StartupImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupImage
        fields = ['url']

class StartupSlidedeckSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupSlidedeck
        fields = ['url']

class StartupBusinessTractionSerializer(serializers.ModelSerializer):
    businessModel = serializers.ListField(child=serializers.CharField(), source="get_business_model_list")
    businessRevenueSources = serializers.CharField(source='business_revenue_sources')
    topCustomers = serializers.SerializerMethodField(method_name="get_topCustomers")
    
    def get_topCustomers(self, obj):
        if obj.top_customers:
            top_customers_serializer =StartupTopCustomerSerializer(obj.top_customers,many=True)
            return top_customers_serializer.data
        else:
            return []
    
    class Meta:
        model = StartupBusinessTraction
        fields = ['businessModel', 'businessRevenueSources','mrr', 'topCustomers']

class StartupTopCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupTopCustomer
        fields = ['name', 'url']

class TopCustomerCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=max_length_name,required=True)
    url = serializers.URLField(max_length=max_length_url,required=False, allow_blank=True, allow_null=True)

class StartupBusinessTractionCreateSerializer(serializers.Serializer):
    businessModel = serializers.ListField(child=serializers.ChoiceField(choices=StartupBusinessTraction.BUSINESS_MODEL_CHOICE))
    businessRevenueSources = serializers.ChoiceField(choices=StartupBusinessTraction.REVENUE_SOURCES_CHOICE)
    mrr = serializers.IntegerField()
    topCustomers = TopCustomerCreateSerializer(many=True)
    
    def validate_businessModel(self, value):
        """Validate that the business models are not empty."""
        if not value:
            raise serializers.ValidationError("At least one business model must be selected.")
        return value
    
    def create(self, validated_data):
        validated_data['businessModel'] = validated_data['businessModel'].split(",")
        return super().create(validated_data)

class StartupBusinessTractionEditSerializer(serializers.Serializer):
    businessModel = serializers.ListField(child=serializers.ChoiceField(choices=StartupBusinessTraction.BUSINESS_MODEL_CHOICE))
    businessRevenueSources = serializers.ChoiceField(choices=StartupBusinessTraction.REVENUE_SOURCES_CHOICE, required=False)
    mrr = serializers.IntegerField(required=False)
    topCustomers = TopCustomerCreateSerializer(many=True, required=False)
    
    def validate_businessModel(self, value):
        """Validate that the business models are not empty."""
        if not value:
            raise serializers.ValidationError("At least one business model must be selected.")
        return value
    
    def create(self, validated_data):
        validated_data['businessModel'] = validated_data['businessModel'].split(",")
        return super().create(validated_data)

class FounderSerializer(serializers.ModelSerializer):
    firstName = serializers.SerializerMethodField(method_name="get_firstName")
    lastName = serializers.SerializerMethodField(method_name="get_lastName")
    pictureUrl = serializers.SerializerMethodField(method_name="get_pictureUrl")
    isConfirmed = serializers.BooleanField(source="is_confirmed")
    isMain = serializers.BooleanField(source="is_main")
    
    def get_firstName(self, obj):
        return obj.first_name if not obj.user else obj.user.first_name
    
    def get_lastName(self, obj):
        return obj.last_name if not obj.user else obj.user.last_name
    
    def get_pictureUrl(self, obj):
        return None if not obj.user else obj.user.picture_url
    
    class Meta:
        model = Founder
        fields = [
            'id', 
            'firstName',
            'lastName',
            'pictureUrl',
            'role',
            'email',
            'isConfirmed',
            'isMain'
            ]
        
class FounderCreateSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=max_length_name,required=True)
    lastName = serializers.CharField(max_length=max_length_name,required=True)
    email = serializers.EmailField(max_length=max_length_email,required=True)
    role = serializers.CharField(max_length=max_length_name,required=False, allow_blank=False)

class FounderEditSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=max_length_name,required=False, allow_blank=False)
    lastName = serializers.CharField(max_length=max_length_name,required=False, allow_blank=False)
    role = serializers.CharField(max_length=max_length_name,required=False, allow_blank=False)
    email = serializers.EmailField(max_length=max_length_email,required=False, allow_blank=False)
    
    def validate(self, data):
        founder = self.context.get('founder')
        if founder:
            if founder.is_confirmed:
                if not data.get('role'):
                    raise serializers.ValidationError({"role": "This field is required when the founder is confirmed."})
        return data

class FounderConfirmSerializer(serializers.Serializer):
    confirm = serializers.BooleanField()

class StartupSerializer(serializers.ModelSerializer):
    mainFunder = serializers.SerializerMethodField(method_name="get_mainFunder")
    videoUrl = serializers.SerializerMethodField(method_name="get_videoUrl")
    imageUrl = serializers.SerializerMethodField(method_name="get_imageUrl")
    businessTractions = serializers.SerializerMethodField(method_name="get_businessTractions")
    founders = serializers.SerializerMethodField(method_name="get_founders")
    websiteUrl = serializers.URLField(source="website_url")
    employeeCount = serializers.URLField(source="employee_count")
    hasInvestors = serializers.SerializerMethodField(method_name="get_investors")
    pitchDeckUrl = serializers.SerializerMethodField(method_name="get_pitchDeckUrl")
    location = serializers.SerializerMethodField(method_name="get_location")
    foundationDate = serializers.DateField(source="foundation_date")
    isPublic = serializers.BooleanField(source="is_public")
    isAbleToShare = serializers.SerializerMethodField(method_name="get_isAbleToShare")
    industry = serializers.SerializerMethodField(method_name="get_industry")
    techSector = serializers.SerializerMethodField(method_name="get_techSector")
    plan = serializers.SerializerMethodField(method_name="get_plan")

    def get_founders(self,obj):
        co_founders = Founder.objects.filter(startup_id=obj.id).order_by('created_at')
        list_founder = FounderSerializer(co_founders,many=True).data
        return list_founder
        
    def get_mainFunder(self, obj):
        user_serializer = SmallUserSerializer(obj.main_founder)
        return user_serializer.data
    
    def get_videoUrl(self, obj):
        video = StartupVideo.objects.filter(startup = obj, is_active=True)
        if video:
            return video[0].url
        else:
            return None
        
    def get_imageUrl(self, obj):
        image = StartupImage.objects.filter(startup=obj, is_active=True)
        if image:
            return image[0].url
        else:
            return None
    
    def get_location(self, obj):
        location = StartupLocation.objects.get(startup=obj)
        if location:
            return location.full_name
    
    def get_businessTractions(self, obj):
        business_traction = StartupBusinessTraction.objects.filter(startup=obj)
        if business_traction:
            business_tractions_serializer = StartupBusinessTractionSerializer(business_traction[0])
            return business_tractions_serializer.data
        else:
            None
    
    def get_investors(self, obj):
        return InvestmentRound.objects.filter(startup=obj).exists()
    
    def get_pitchDeckUrl(self, obj):
        pitch_deck = StartupSlidedeck.objects.filter(startup=obj, is_active=True)
        if pitch_deck:
            return pitch_deck[0].url
        else:
            return None
    
    def get_isAbleToShare(self, obj):
        investors = self.get_investors(obj)
        business_tractions= self.get_businessTractions(obj)
        pitch_deck_url = self.get_pitchDeckUrl(obj)
        is_able_share = False
        if investors is not None and business_tractions is not None  and pitch_deck_url is not None and obj.description is not None :
            is_able_share = True
        return is_able_share
    
    def get_industry(self, obj):
        if obj.industry_category:
            return StartupSubcategorySerializer(obj.industry_category).data
        else:
            return None
    
    def get_techSector(self, obj):
        if obj.tech_sector:
            return StartupTechSectorSerializer(obj.tech_sector).data
        else:
            return None
    
    def get_plan(self, obj):
        subscription = Subscription.objects.filter(startup=obj).first()
        if subscription:
            return subscription.stripe_subscription_status

        return Subscription.BASIC
        
    class Meta:
        model = Startup
        fields = [
            'id', 
            'name',
            'mainFunder',
            'description', 
            'location',
            'businessTractions',
            'founders',
            'foundationDate',
            'industry',
            'techSector',
            'employeeCount', 
            'stage', 
            'websiteUrl',
            'videoUrl',
            'imageUrl',
            'hasInvestors',
            'pitchDeckUrl',
            'isPublic',
            'isAbleToShare',
            'plan',
            ]

class StartupSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Startup
        fields = ['id', 'name']

class CreateStartupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=max_length_name)
    description = serializers.CharField(max_length=max_length_description,allow_blank=True,allow_null=True, required=False)
    location = serializers.CharField(max_length=max_length_location)
    industry = serializers.CharField(max_length=max_length_industry)
    techSector = serializers.CharField(max_length=max_length_industry, allow_blank=True, required = False)
    employeeCount = serializers.ChoiceField(choices=Startup.EMPLOYEE_COUNT_CHOICE)
    stage = serializers.ChoiceField(choices=Startup.STAGE_CHOICE, allow_blank=True, required = False)
    foundationDate = serializers.DateField(allow_null=True, required = False)
    websiteUrl = serializers.CharField(max_length=max_length_url, allow_blank=True, required = False)
    
    def validate_location(self, value):
        pattern = r'^[a-zA-ZÀ-ÿ\s-]+,\s[a-zA-ZÀ-ÿ\s-]+,\s[a-zA-Z\s]+$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("The location must be in the 'City, State, Country' format.")
        return value
    
    def validate_industry(self, value):
        if not StartupSubcategory.objects.filter(id=value):
            raise serializers.ValidationError("Invalid industry")
        return value
    
    def validate_techSector(self, value):
        if not StartupTechSector.objects.filter(id=value):
            raise serializers.ValidationError("Invalid Tech Sector")
        return value

class EditStartupStageSerializer(serializers.Serializer):
    stage  = serializers.ChoiceField(choices=Startup.STAGE_CHOICE, required = True, allow_blank=False)

class EditStartupLocationSerializer(serializers.Serializer):
    location  = serializers.CharField(max_length = max_length_location, allow_blank= False, required = True)
    
    def validate_location(self, value):
        pattern = r'^[a-zA-ZÀ-ÿ\s-]+,\s[a-zA-ZÀ-ÿ\s-]+,\s[a-zA-Z\s]+$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("The location must be in the 'City, State, Country' format.")
        return value

class EditStartupNameSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=max_length_name, required=True, allow_blank=False)

class EditStartupIndustrySerializer(serializers.Serializer):
    industry = serializers.CharField(max_length=max_length_industry, required=True, allow_blank=False)

    def validate_industry(self, value):
        if not StartupSubcategory.objects.filter(id=value):
            raise serializers.ValidationError("TInvalid industry")
        return value

class EditPrivacySerializer(serializers.Serializer):
    isPrivacy = serializers.BooleanField()

class EditStartupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=max_length_name,required=False, allow_blank=True)
    location = serializers.CharField(max_length=max_length_location,required=False, allow_blank=True)
    industry = serializers.CharField(max_length=max_length_industry,required=False, allow_blank=True)
    techSector = serializers.CharField(max_length=max_length_industry,required=False, allow_blank=True)
    foundationDate = serializers.DateField(allow_null=True, required = False)
    employeeCount = serializers.ChoiceField(choices=Startup.EMPLOYEE_COUNT_CHOICE,required=False, allow_blank=True)
    stage = serializers.ChoiceField(choices=Startup.STAGE_CHOICE,required=False, allow_blank=True)
    websiteUrl = serializers.URLField(max_length=max_length_url,required=False, allow_blank=True)
    
    def validate_location(self, value):
        pattern = r'^[a-zA-ZÀ-ÿ\s-]+,\s[a-zA-ZÀ-ÿ\s-]+,\s[a-zA-Z\s]+$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("The location must be in the 'City, State, Country' format.")
        return value
    
    def validate_industry(self, value):
        if not StartupSubcategory.objects.filter(id=value):
            raise serializers.ValidationError("Invalid industry")
        return value
    
    def validate_techSector(self, value):
        if not StartupTechSector.objects.filter(id=value):
            raise serializers.ValidationError("Invalid Tech Sector")
        return value


class EditStartupWebsiteSerializer(serializers.Serializer):
    websiteUrl = serializers.URLField(max_length=max_length_url, required=True, allow_blank=False)

class EditStartupImageSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True, allow_empty_file=False)

    def validate(self, data):
        if not data:
            raise serializers.ValidationError("Image field cannot be empty")
        return data

class EditStartupDescriptionSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=max_length_description, required=True, allow_blank=False)

class StartupCreatePitchDeckSerializer(serializers.Serializer):
    pitchDeck = serializers.FileField(required=True, allow_empty_file=False)

    def validate_pitchDeck(self, value):
        if not value:
            raise serializers.ValidationError("Pitch Deck File cannot be empty")
        return value
    
class EditStartupVideoSerializer(serializers.Serializer):
    video = serializers.FileField(required=True,allow_empty_file=False)

    def validate_video(self, value):
        if not value:
            raise serializers.ValidationError("Video field cannot be empty")
        return value

class EditStartupFoundationDateSerializer(serializers.Serializer):
    foundationDate = serializers.DateField(required = True)
 
class CreateStartupShareSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=max_length_name,required=True)
    lastName = serializers.CharField(max_length=max_length_name,required=True)
    email = serializers.EmailField(max_length=max_length_email,required=True)
    relationship = serializers.CharField(max_length=max_length_name,required=True)
    
class CreateVisitorSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=max_length_email,required=True)
    isTermsAcepted = serializers.BooleanField()

class CreatePrivateVisitorSerializer(serializers.Serializer):
    isTermsAcepted = serializers.BooleanField()
    
class FounderDynamicSerializer(serializers.BaseSerializer):
    
    def to_representation(self, obj):
        if obj.user:
            serializer = ProfileSerializer(obj.user)
            result_founder = serializer.data
            result_founder['role'] = obj.role
        else:
            serializer = FounderSerializer(obj)
            result_founder = serializer.data
        
        return result_founder

class DetailedOutsiderStartupViewerSerializer(serializers.ModelSerializer):
    mainFunder = serializers.SerializerMethodField(method_name="get_mainFunder")
    videoUrl = serializers.SerializerMethodField(method_name="get_videoUrl")
    imageUrl = serializers.SerializerMethodField(method_name="get_imageUrl")
    businessTractions = serializers.SerializerMethodField(method_name="get_businessTractions")
    founders = serializers.SerializerMethodField(method_name="get_founders")
    websiteUrl = serializers.URLField(source="website_url")
    employeeCount = serializers.URLField(source="employee_count")
    foundationDate = serializers.DateField(source="foundation_date")
    pitchDeckUrl = serializers.SerializerMethodField(method_name="get_pitchDeckUrl")
    InvestmentRounds = serializers.SerializerMethodField(method_name="get_list_investment_rounds")
    location = serializers.SerializerMethodField(method_name="get_location")
    industry = serializers.SerializerMethodField(method_name="get_industry")
    techSector = serializers.SerializerMethodField(method_name="get_techSector")

    def get_list_investment_rounds(self, obj): 
        startup = Startup.objects.get(id=obj.id)
        nvestors = InvestmentRound.objects.filter(startup= startup, is_active=True)
        serializer = InvestmentRoundSerializer(nvestors, many=True)
        return serializer.data

    def get_founders(self,obj):
        co_founders = Founder.objects.filter(startup_id=obj.id).order_by('created_at')
        list_founder = FounderDynamicSerializer(co_founders,many=True).data
        return list_founder
        
    def get_mainFunder(self, obj):
        user_serializer = SmallUserSerializer(obj.main_founder)
        return user_serializer.data
    
    def get_videoUrl(self, obj):
        video = StartupVideo.objects.filter(startup = obj, is_active=True)
        if video:
            return video[0].url
        else:
            return None
        
    def get_imageUrl(self, obj):
        image = StartupImage.objects.filter(startup=obj, is_active=True)
        if image:
            return image[0].url
        else:
            return None
    
    def get_businessTractions(self, obj):
        business_traction = StartupBusinessTraction.objects.filter(startup=obj)
        if business_traction:
            business_tractions_serializer = StartupBusinessTractionSerializer(business_traction[0])
            return business_tractions_serializer.data
        else:
            None
    
    def get_investors(self, obj):
        return InvestmentRound.objects.filter(startup=obj).exists()
    
    def get_pitchDeckUrl(self, obj):
        pitch_deck = StartupSlidedeck.objects.filter(startup=obj, is_active=True)
        if pitch_deck:
            return pitch_deck[0].url
        else:
            return None
    
    def get_location(self, obj):
        location = StartupLocation.objects.get(startup=obj)
        if location:
            return location.full_name
    
    def get_industry(self, obj):
        if obj.industry_category:
            return StartupSubcategorySerializer(obj.industry_category).data
        else:
            return None
    
    def get_techSector(self, obj):
        if obj.tech_sector:
            return StartupTechSectorSerializer(obj.tech_sector).data
        else:
            return None
    
    
    class Meta:
        model = Startup
        fields = [
            'id', 
            'name',
            'mainFunder',
            'description',
            'businessTractions',
            'founders',
            'industry', 
            'employeeCount',
            'foundationDate',
            'stage',
            'websiteUrl',
            'videoUrl',
            'imageUrl',
            'pitchDeckUrl',
            'InvestmentRounds',
            'location',
            'techSector'
            ]

class StartupSubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupSubcategory
        fields = ['id', 'name']

class StartupCategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = StartupCategory
        fields = ['id', 'name']
        
class StartupTechSectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupTechSector
        fields = ['id', 'name']