from django.test import TestCase
from django.contrib.auth import get_user_model
from investors.models import InvestmentRound
from startups.models import Startup, StartupCategory, StartupSubcategory
from pjbackend.constants import INDUSTRIES_CATEGORIES, INDUSTRIES_SUBCATEGORIES
import pytest

User = get_user_model()

@pytest.mark.django_db
class InvestorModelTests(TestCase):
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
        self.user = User.objects.create(
            email="test@example.com",
            password="testpass123",
            phone_number="+123456789",
            linkedin_url="https://www.linkedin.com/in/testuser",
            x_url="http://x.com/profile/testuser",
            website_url="http://testuser.com",
            calendly_url="http://calendly.com/testuser",
            bio="Test bio.",
        )
        self.startup = Startup.create_startup_for_test(
            name="PomJuice",
            main_founder=self.user,
            description="description startup",
            employee_count=Startup.ONE_TO_TEN,
            industry_category=self.subcategory,
            stage="Pre-Seed",
            website_url="https://pomjuice.com",
            is_active=True,
        )

    def test_investment_round_creation(self):
        round = InvestmentRound.objects.create(
            startup=self.startup,
            round_type="Seed",

            amount=50000,
            raised_amount=50000,
            is_active=True,
        )
        self.assertEqual(round.startup.name, "PomJuice")
        self.assertEqual(round.round_type, "Seed")
        self.assertEqual(round.amount, 50000)
        self.assertTrue(round.is_active)
        self.assertEqual(round.raised_amount, 50000)
