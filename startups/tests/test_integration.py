from django.test import TestCase
from django.contrib.auth import get_user_model
from startups.models import Startup, StartupShare, Founder, StartupCategory, StartupSubcategory, StartupTechSector
from pjbackend.constants import INDUSTRIES_CATEGORIES, INDUSTRIES_SUBCATEGORIES, TECH_SECTOR
from users.models import CustomUser
from reviews.models import Review
from investors.models import InvestmentRound
from django.utils import timezone

User = get_user_model()


class StartupIntegrationTest(TestCase):
    def setUp(self):
        self.category = StartupCategory.objects.create(
            name = INDUSTRIES_CATEGORIES[0].get("name"),
            code = INDUSTRIES_CATEGORIES[0].get("code")
        )
        subcategories = INDUSTRIES_SUBCATEGORIES.get(self.category.code)
        self.subcategory = StartupSubcategory.objects.create(
            name = subcategories[0].get("name"),
            code = subcategories[0].get("code"),
            category = self.category 
        )
        self.tech_sector = StartupTechSector.objects.create(
            name = TECH_SECTOR[0].get("name")
        )
        # Create a user instance for the main founder of the startup
        self.founder = CustomUser.objects.create(
            email="john-doe@email.com",
            password="testpass123",
            phone_number="+1234567890",
            linkedin_url="http://linkedin.com/in/johndoe",
        )
          # Create a startup instance
        self.startup = Startup.create_startup_for_test(
            name="Innovative Startup",
            main_founder=self.founder,
            description="A disruptive startup.",
            location="Bessemer, Alabama, United States",
            industry_category=self.subcategory,
            tech_sector =self.tech_sector,
            employee_count=Startup.TEN_TO_FIFTY,
            stage="Seed",
            website_url="https://innovativestartup.com",
            is_active=True,
        )
      
        self.cofounder1 = CustomUser.objects.create(
            email="james-doe@email.com",
            password="testpass123",
            phone_number="+1234567891",
            linkedin_url="http://linkedin.com/in/jamesdoe",
        )

        self.cofounder2 = CustomUser.objects.create(
            email="alex-doe@email.com",
            password="testpass123",
            phone_number="+1234567892",
            linkedin_url="http://linkedin.com/in/alexdoe",
        )
        Founder.objects.create(
            user=self.cofounder1,
            startup=self.startup,
            first_name="James",
            last_name="Doe",
            is_confirmed=True  # Assuming they are already accepted
        )

        Founder.objects.create(
            user=self.cofounder2,
            startup=self.startup,
            first_name="Alex",
            last_name="Doe",
            is_confirmed=True  # Assuming they are already accepted
        )

      

        # Create an investor user and firm
        self.investor_user = CustomUser.objects.create(
            email="investor@example.com",
            password="testpass123",
            phone_number="+1234567890",
            linkedin_url="http://linkedin.com/in/johndoe",
        )
        
        # Create investment round linking the startup with the investor firm
        self.investment_round = InvestmentRound.objects.create(
            startup=self.startup,
            round_type="Series A",
            amount=1000000,
            raised_amount=1000000,
            date=timezone.now().date(),
            is_active=True,
        )

        # Create a review for the startup
        self.review = Review.objects.create(
            email=self.investor_user.email,
            startup=self.startup,
            overal_rating=5,
            details="Great potential!",
            is_anonymous=False,
            is_active=True,
        )

    def test_startup_review_relationship(self):
        # Verify the startup has the correct review
        self.assertEqual(self.review.startup, self.startup)
        self.assertEqual(self.review.email, self.investor_user.email)
        self.assertEqual(self.review.overal_rating, 5)


    def test_startup_founder_relationship(self):  # NEED TO FIX
        # Verify the startup has the correct main founder
        self.assertEqual(self.startup.main_founder, self.founder)
        self.assertEqual(self.founder.main_founder_of.first(), self.startup)

    def test_startup_cofounder_relationship(self):  # NEED TO FIX
        cofounders = Founder.objects.filter(startup=self.startup, is_confirmed = True)
        cofounders_users = [cofounder.user for cofounder in cofounders]
        self.assertIn(self.cofounder1, cofounders_users)
        self.assertIn(self.cofounder2, cofounders_users)

        # Verify the number of co-founders matches
        self.assertEqual(cofounders.count(), 3)

        # Verify the co-founders are not the main founder
        self.assertNotEqual(self.startup.main_founder, self.cofounder1)
        self.assertNotEqual(self.startup.main_founder, self.cofounder2)
    
    def test_investor_invitation_to_startup(self):  
        # Create an instance of StartupShare or similar to represent an invitation
        # Inviting Investor to view the startup information
        share = StartupShare.objects.create(
            startup=self.startup,
            first_name=self.investor_user.first_name,
            last_name=self.investor_user.last_name,
            email=self.investor_user.email,
            relationship="Investor",
            url="https://example.com/share",
        )
        self.assertEqual(share.startup, self.startup)
        self.assertEqual(share.first_name, self.investor_user.first_name)
        self.assertEqual(share.last_name, self.investor_user.last_name)
        self.assertEqual(share.email, self.investor_user.email)
        self.assertEqual(share.relationship, "Investor")
    
    #  Verify the share is linked to the correct startup
    # self.assertEqual(share.startup, self.startup)
    # Optionally, test the content of the invitation or the process of accepting it
