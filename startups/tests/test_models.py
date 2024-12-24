from django.test import TestCase
from users.models import CustomUser

from startups.models import (
    StartupCategory,
    StartupSubcategory,
    Startup,
    StartupVideo,
    StartupImage,
    StartupSlidedeck,
    StartupBusinessTraction,
    StartupTopCustomer,
    Founder,
)
from startups.models import StartupShare

from pjbackend.constants import INDUSTRIES_CATEGORIES, INDUSTRIES_SUBCATEGORIES

class StartupModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Define common user attributes
        email = "john-doe@email.com"
        password = "testpass123"
        phone_number = "+1234567890"
        linkedin_url = "http://linkedin.com/in/johndoe"
        
        cls.category = StartupCategory.objects.create(
            name = INDUSTRIES_CATEGORIES[0].get("name"),
            code = INDUSTRIES_CATEGORIES[0].get("code")
        )
        subcategories = INDUSTRIES_SUBCATEGORIES.get(cls.category.code)
        cls.subcategory = StartupSubcategory.objects.create(
            name = subcategories[0].get("name"),
            code = subcategories[0].get("code"),
            category = cls.category 
        )

        # Create a common user for use in all test methods
        cls.user = CustomUser.objects.create(
            email=email,
            password=password,
            phone_number=phone_number,
            linkedin_url=linkedin_url,
        )

        # Define startup attributes
        startup_name = "Test Startup"
        description = "Test Description"
        location = "Bessemer, Alabama, United States"
        employee_count = Startup.ONE_TO_TEN
        stage = "Seed"
        website_url = "http://teststartup.com"
        is_active = True

        # Create a startup
        cls.startup = Startup.create_startup_for_test(
            name=startup_name,
            main_founder=cls.user,
            description=description,
            location=location,
            industry_category=cls.subcategory,
            employee_count=employee_count,
            stage=stage,
            website_url=website_url,
            is_active=is_active,
        )

    def test_startup_creation(self):
        # Validate the startup was created successfully
        self.assertEqual(self.startup.name, "Test Startup")
        self.assertEqual(self.startup.main_founder, self.user)
        self.assertEqual(self.startup.employee_count, Startup.ONE_TO_TEN)
        self.assertEqual(self.startup.employee_count, Startup.ONE_TO_TEN)
        self.assertEqual(self.startup.industry_category, self.subcategory)

    # Remaining test methods remain unchanged

    def test_startup_string_representation(self):
        # Test the custom __str__ method for Startup model
        self.assertEqual(str(self.startup), "Test Startup")

    def test_related_models(self):
        # Test creating and associating StartupVideo, StartupImage, and StartupSlidedeck with Startup
        StartupVideo.objects.create(startup=self.startup, url="http://video.com")
        StartupImage.objects.create(startup=self.startup, url="http://image.com")
        StartupSlidedeck.objects.create(
            startup=self.startup, url="http://slidedeck.com"
        )

        self.assertEqual(self.startup.video.first().url, "http://video.com")
        self.assertEqual(self.startup.image.first().url, "http://image.com")
        self.assertEqual(self.startup.slidedeck.first().url, "http://slidedeck.com")

    def test_business_traction(self):
        # Test creating StartupBusinessTraction and associating it with Startup
        StartupBusinessTraction.objects.create(
            startup=self.startup,
            business_model=StartupBusinessTraction.SAAS,
            business_revenue_sources=StartupBusinessTraction.B2C,
            mrr=1000,
        )
        business_traction = StartupBusinessTraction.objects.get(startup=self.startup)
        self.assertEqual(business_traction.business_model, StartupBusinessTraction.SAAS)
        self.assertEqual(business_traction.mrr, 1000)

    def test_top_customer(self):
        # Test creating StartupTopCustomer and associating it with Startup
        StartupTopCustomer.objects.create(
            startup=self.startup, name="Top Customer", url="http://topcustomer.com"
        )
        top_customer = self.startup.top_customers.first()
        self.assertEqual(top_customer.name, "Top Customer")

    def test_founder(self):
        # Test creating Founder and associating it with Startup and User
        founder = Founder.objects.create(
            startup=self.startup, user=self.user, is_confirmed=True
        )
        cofounder = Founder.objects.create(
            startup=self.startup, user=self.user, is_confirmed= False
        )
        self.assertEqual(founder.user, self.user)
        self.assertEqual(founder.startup, self.startup)
        self.assertEqual(founder.user.first_name, self.user.first_name)
        self.assertEqual(founder.user.last_name, self.user.last_name)
        self.assertEqual(founder.is_confirmed, True)
        #Tests for cofounders if any.
        self.assertEqual(cofounder.user, self.user)
        self.assertEqual(cofounder.startup, self.startup)
        self.assertEqual(cofounder.user.first_name, self.user.first_name)
        self.assertEqual(cofounder.user.last_name, self.user.last_name)
        self.assertEqual(cofounder.is_confirmed, False)

   
    def test_startup_share_creation(self):
        # Defining Sample Data which represent the data entered by the startup founder to share their startup.
        first_name = "Jane"
        last_name = "Doe"
        email = "jane.doe@example.com"
        relationship = "Friend"
        url = "http://share.com"
        
        
        # Create a startup share instance
        startup_share = StartupShare.objects.create(
            startup=self.startup,
            first_name=first_name,
            last_name=last_name,
            email=email,
            relationship=relationship,
            url=url,
        )

        # Validate the startup share was created successfully
        self.assertEqual(startup_share.startup, self.startup)
        self.assertEqual(startup_share.first_name, first_name)
        self.assertEqual(startup_share.last_name, last_name)
        self.assertEqual(startup_share.email, email)
        self.assertEqual(startup_share.relationship, relationship)
        self.assertEqual(startup_share.url, url)
        # self.assertIn(startup_share.relationship, [choice[0] for choice in StartupShare.RELATIONSHIP_CHOICES])

    # Validate the startup share was created successfully
