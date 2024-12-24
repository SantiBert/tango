import uuid
import stripe
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import PrivateVisitorManager
from payment.models import Subscription

max_length_name = settings.MAX_LENGTH_CONFIG['names']
max_length_email = settings.MAX_LENGTH_CONFIG['email']
max_length_url = settings.MAX_LENGTH_CONFIG['url']
max_length_relationship = settings.MAX_LENGTH_CONFIG['relationship']
max_length_business_model = settings.MAX_LENGTH_CONFIG['business_model']
max_length_industry = settings.MAX_LENGTH_CONFIG['industry']
max_length_location = settings.MAX_LENGTH_CONFIG['location']

stripe.api_key = settings.STRIPE_SECRET_KEY


class StartupCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=max_length_name)
    code = models.CharField(max_length=max_length_name, unique=True)

    def __str__(self):
        return self.name

class StartupSubcategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=max_length_name)
    code = models.CharField(max_length=max_length_name, unique=True)
    category = models.ForeignKey(StartupCategory, related_name='subcategories', on_delete=models.PROTECT)

    def __str__(self):
        return self.name
    
class StartupTechSector(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=max_length_name)

    def __str__(self):
        return self.name

class Startup(models.Model):

    ONE_TO_TEN = "1 - 10"
    TEN_TO_FIFTY = "10 - 50"
    FIFTY_TO_TWOHUNDREDFIFTY = "50 - 250"
    MORE_TWOHUNDREDFIFTY = "+ 250"

    SEED = "Seed"
    PRE_SEED = "Pre-Seed"
    SERIES_A = "Series A"
    SERIES_B = "Series B"
    SERIES_C = "Series C"
    SERIES_D = "Series D"
     
    EMPLOYEE_COUNT_CHOICE = (
        (ONE_TO_TEN, "1 - 10"),
        (TEN_TO_FIFTY, "10 - 50"),
        (FIFTY_TO_TWOHUNDREDFIFTY, "50 - 250"),
        (MORE_TWOHUNDREDFIFTY, "+ 250"),
    )

    EMPLOYEE_COUNT_DICT = {
        ONE_TO_TEN: [i for i in range(1, 10)],
        TEN_TO_FIFTY: [i for i in range(10, 50)],
        FIFTY_TO_TWOHUNDREDFIFTY: [i for i in range(50, 250)],
        MORE_TWOHUNDREDFIFTY: 251,
    }
    
    STAGE_CHOICE = (
        (SEED,"Seed"),
        (PRE_SEED, "Pre-Seed"),
        (SERIES_A, "Series A"),
        (SERIES_B, "Series B"),
        (SERIES_C, "Series C"),
        (SERIES_D, "Series D"),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    main_founder = models.ForeignKey(
        "users.CustomUser", 
        on_delete=models.PROTECT, 
        related_name="main_founder_of", 
        null=True
    )
    description = models.TextField(blank=True, null=True)
    industry_category = models.ForeignKey(
        StartupSubcategory, 
        on_delete=models.PROTECT, 
        related_name="industry", 
        blank=True, 
        null=True
    )
    employee_count = models.CharField(
        choices=EMPLOYEE_COUNT_CHOICE,
        default=ONE_TO_TEN,
        blank=True,
        null=True,
        max_length=20,
    )
    stage = models.CharField(
        choices=STAGE_CHOICE,
        blank=True, 
        null=True,
        max_length=20
    )
    tech_sector = models.ForeignKey(
        StartupTechSector, 
        on_delete=models.PROTECT, 
        related_name="tech_sector", 
        blank=True, 
        null=True
    )
    website_url = models.URLField(blank=True, null=True, max_length=max_length_url)
    foundation_date = models.DateField(blank=True, null=True)
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)  
    
    def __str__(self):
        return self.name

    def user_has_access(self, user):
        founders = self.founders.filter(is_confirmed=True)
        founder_ids = [founder.user_id for founder in founders]
        founder_ids.append(self.main_founder.id)
        return user.id in founder_ids
    
    @classmethod
    def create_startup(cls, **kwargs):
        location = kwargs.pop('location', None)
        startup = cls.objects.create(**kwargs)
        
        if location:
            city, state, country = location.split(", ")
            StartupLocation.objects.create(
                startup=startup,
                full_name=location,
                city_name=city.strip(),
                state_name=state.strip(),
                country_name=country.strip()
            )
        
        Founder.objects.create(
            user=startup.main_founder,
            startup=startup,
            email=startup.main_founder.email,
            first_name=startup.main_founder.first_name,
            last_name=startup.main_founder.last_name,
            role='Main Founder',
            is_confirmed=True,
            is_main = True
        )
        
        stripe_customer = stripe.Customer.create(
            email=startup.main_founder.email,
            name=startup.name
        )

        stripe_trial_subscription = stripe.Subscription.create(
            customer=stripe_customer['id'],
            items=[{'price': settings.PRO_ANNUAL_ID}], 
            trial_period_days=14,
            metadata={
                'startup_id': startup.id,
                'user_id': startup.main_founder.id  
            }
        )

        Subscription.objects.create(
            startup=startup,
            stripe_customer_id=stripe_customer['id'],
            stripe_subscription_id=stripe_trial_subscription['id'],
            stripe_subscription_status=Subscription.TRIAL,
            stripe_trial_end_date=timezone.now() + timedelta(days=14)
        )
        
        return startup
    
    @classmethod
    def create_startup_for_test(cls, **kwargs):
        location = kwargs.pop('location', None)
        startup = cls.objects.create(**kwargs)
        
        if location:
            city, state, country = location.split(", ")
            StartupLocation.objects.create(
                startup=startup,
                full_name=location,
                city_name=city.strip(),
                state_name=state.strip(),
                country_name=country.strip()
            )
        
        Founder.objects.create(
            user=startup.main_founder,
            startup=startup,
            email=startup.main_founder.email,
            first_name=startup.main_founder.first_name,
            last_name=startup.main_founder.last_name,
            role='Main Founder',
            is_confirmed=True,
            is_main = True
        )
        
        return startup

class StartupLocation(models.Model):
    startup = models.ForeignKey(Startup, on_delete=models.PROTECT, related_name="location")
    full_name = models.CharField(max_length=max_length_location)
    city_name = models.CharField(max_length=max_length_location, blank=True, null=True)
    state_name = models.CharField(max_length=max_length_location, blank=True, null=True)
    country_name = models.CharField(max_length=max_length_location, blank=True, null=True)

class StartupVideo(models.Model):
    startup = models.ForeignKey(Startup, on_delete=models.PROTECT, related_name="video")
    url = models.URLField()
    is_active = models.BooleanField(default=True)
    
class StartupImage(models.Model):
    startup = models.ForeignKey(Startup, on_delete=models.PROTECT, related_name="image")
    url = models.URLField()
    is_active = models.BooleanField(default=True)

class StartupSlidedeck(models.Model):
    startup = models.ForeignKey(
        Startup, on_delete=models.PROTECT, related_name="slidedeck"
    )
    url = models.URLField()
    is_active = models.BooleanField(default=True)

class StartupBusinessTraction(models.Model):
    PRODUCT_SALES = "product_sales"
    SERVICE_BASED = "service_based"
    PLATFORM = "platform"
    E_COMMERCE = "e_commerce"
    MARKETPLACE = "marketplace"
    SUBCRIPTION = "subcription"
    SAAS = "saas"
    FREEMIUM = "freemium"
    OTHER = "other"

    BUSINESS_MODEL_CHOICE = (
        (PRODUCT_SALES, _("Product Sales")),
        (SERVICE_BASED, _("Service Based")),
        (PLATFORM, _("Platform")),
        (E_COMMERCE, _("E-Commerce")),
        (MARKETPLACE, _("Marketplace")),
        (SUBCRIPTION, _("Subscription")),
        (SAAS, _("Saas")),
        (FREEMIUM, _("Freemium")),
        (OTHER, _("Other")),
    )
    B2B = "b2b"
    B2C = "b2c"
    B2B2C = "b2b2c"
    REVENUE_SOURCES_CHOICE = ((B2B, "B2B"), (B2C, "SB2C"), (B2B2C, "B2B2C"))
    startup = models.OneToOneField(
        Startup,
        related_name="business_tractions", 
        on_delete=models.PROTECT, 
        primary_key=True
    )
    business_model = models.CharField(
        blank=True,
        null=True,
        max_length=50,
    )
    business_revenue_sources = models.CharField(
        choices=REVENUE_SOURCES_CHOICE,
        default=B2B,
        blank=True,
        null=True,
        max_length=max_length_business_model,
    )
    mrr = models.IntegerField(blank=True, null=True)
    
    def get_business_model_list(self):
        """Returns the business models as a list of values."""
        if self.business_model:
            return self.business_model.split(",")
        return []

    def set_business_model_list(self, model_list):
        """Sets the business models from a list of values."""
        if isinstance(model_list, list):
            self.business_model = ",".join(model_list)
        else:
            raise ValueError("model_list must be a list")

    def __str__(self):
        return f"{self.startup} - Business Models: {self.business_model}"


class StartupTopCustomer(models.Model):
    startup = models.ForeignKey(Startup, on_delete=models.PROTECT, related_name="top_customers")
    business_traction = models.ForeignKey(StartupBusinessTraction,on_delete=models.PROTECT, related_name="top_customers",blank=True, null=True)
    name = models.TextField()
    image = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)


class Founder(models.Model):
    user = models.ForeignKey("users.CustomUser", on_delete=models.PROTECT, blank=True, null=True)
    startup = models.ForeignKey(Startup, on_delete=models.PROTECT, related_name="founders")
    email = models.EmailField(max_length=max_length_email,blank=True, null=True)
    first_name = models.CharField(max_length=max_length_name,blank=True, null=True)
    last_name = models.CharField(max_length=max_length_name,blank=True, null=True)
    role = models.CharField(max_length=max_length_name,blank=True, null=True)
    is_confirmed = models.BooleanField(default=False)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)  
    
    def __str__(self):
        return f"Startup ->{self.startup.name}, Founder -> {self.first_name} {self.last_name}"


class StartupShare(models.Model):
    startup = models.ForeignKey(Startup, on_delete=models.PROTECT)
    first_name = models.CharField(max_length=max_length_name)
    last_name = models.CharField(max_length=max_length_name)
    email = models.EmailField(max_length=max_length_email)
    relationship = models.CharField(max_length=max_length_relationship)
    creation_date = models.DateField(auto_now_add=True)
    url = models.URLField(max_length=max_length_url, blank=True, null=True)

    def __str__(self):
        return f"Startup ->{self.startup.name}, Shared whit-> {self.email}"

class PublicVisitor(models.Model):
    email = models.EmailField(max_length=max_length_email)
    device_id = models.CharField(max_length=350,blank=True, null=True)
    startup = models.ForeignKey(Startup, on_delete=models.PROTECT, related_name="public_visitors")
    is_terms_acepted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Startup ->{self.startup.name}, Public Visitor -> {self.email}"    

class PrivateVisitor(models.Model):
    email = models.EmailField(max_length=max_length_email)
    device_id = models.CharField(max_length=350,blank=True, null=True)
    unique_token = models.CharField(max_length=100, unique=True)
    startup = models.ForeignKey(Startup, on_delete=models.PROTECT, related_name="private_visitors")
    is_terms_acepted = models.BooleanField(default=False)
    
    objects = PrivateVisitorManager()
    
    def __str__(self):
        return f"Startup ->{self.startup.name}, Private Visitor -> {self.email}"    