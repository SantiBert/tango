from django.test import TestCase
from reviews.models import Review
from users.models import CustomUser
from startups.models import Startup, StartupCategory, StartupSubcategory
from pjbackend.constants import INDUSTRIES_CATEGORIES, INDUSTRIES_SUBCATEGORIES

class TestReviewModel(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create(
            email="test@gmail.com", password="testpass123"
        )
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
        self.startup = Startup.create_startup_for_test(
            name="PomJuice",
            main_founder=self.user,
            description="A description of the startup",
            employee_count=Startup.ONE_TO_TEN,
            location="Bessemer, Alabama, United States",
            industry_category = self.subcategory,
            stage="Pre-Seed",
            website_url="https://pomjuice.com",
            is_active=True,
        )

    def test_review_creation(self):
        review = Review.objects.create(
            email="test@gmail.com",
            startup=self.startup,
            overal_rating=5,
            team_value=4,
            problem_value=4,
            solution_value=4,
            gtmstrategy_value=3,
            marketopp_value=4,
            details="Great potential",
            is_anonymous=False,
            is_active=True,
        )

        self.assertEqual(review.email, "test@gmail.com")
        self.assertEqual(review.startup, self.startup)
        self.assertEqual(review.overal_rating, 5)
        self.assertFalse(review.is_anonymous)
        self.assertTrue(review.is_active)
