# investors/tests/test_integration.py
from django.test import TestCase
from django.utils import timezone
from users.models import CustomUser
from startups.models import Startup
from investors.models import InvestmentRound


class InvestorStartupIntegrationTestCase(TestCase):
    def setUp(self):
        # Create a user and an investor firm
        self.user = CustomUser.objects.create(
            email="john-doe@email.com",
            password="testpass123",
            phone_number="+1234567890",
            linkedin_url="http://linkedin.com/in/johndoe",
        )

        # Create a startup
        self.startup = Startup.create_startup_for_test(
            name="Innovative Startup",
            main_founder=self.user,
            description="Disrupting industries.",
            location="Bessemer, Alabama, United States",
            industry="Technology",
            employee_count=Startup.TEN_TO_FIFTY,
            stage="Seed",
            website_url="https://innovativestartup.com",
            is_active=True,
        )

        # Create an investment round linking the firm and the startup
        self.investment_round = InvestmentRound.objects.create(
            startup=self.startup,
            round_type="Series A",
            amount=1000000,
            raised_amount=1000000,
            date=timezone.now().date(),
            is_active=True,
        )
