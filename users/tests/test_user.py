from django.test import TestCase
from users.models import CustomUser, Experience



class CustomUserModelTest(TestCase):

    def test_create_user(self):
        user = CustomUser.objects.create(
            email="test@example.com",
            password="testpass123",
            phone_number="+1234567890",
            linkedin_url="https://www.linkedin.com/in/testuser",
            x_url="http://x.com/profile/testuser",
            website_url="http://testuser.com",
            calendly_url="http://calendly.com/testuser",
            bio="Test bio.",
            picture_url="https://unsplash.com/photos/brown-tiger-close-up-photo-8Myh76_3M2U",
        )
        self.assertEqual(str(user), "test@example.com")
        self.assertEqual(user.picture_url, "https://unsplash.com/photos/brown-tiger-close-up-photo-8Myh76_3M2U")
        self.assertEqual(user.password, "testpass123")
        self.assertEqual(user.phone_number, "+1234567890")
        self.assertEqual(user.linkedin_url, "https://www.linkedin.com/in/testuser")
        self.assertEqual(user.x_url, "http://x.com/profile/testuser")
        self.assertEqual(user.website_url, "http://testuser.com")
        self.assertEqual(user.calendly_url, "http://calendly.com/testuser")
        self.assertTrue(user.bio, "Test bio.")
    
    def test_experience_model(self):
        user = CustomUser.objects.create(email="test@example.com", password="testpass123")
        experience = Experience.objects.create(
            user=user,
            #description={"role": "Developer", "company": "Test Corp"},
            title="Software Developer",
            company="Test Corp",
            start_date="2021-01-01T00:00:00Z",
            end_date="2021-12-31T00:00:00Z",
        )
        self.assertEqual(experience.user, user)
        #self.assertTrue("Developer" in experience.description["role"])
        self.assertEqual(experience.title, "Software Developer")
        self.assertEqual(experience.company, "Test Corp")
        self.assertEqual(
            str(experience), f"User ->{user.email}, Experience-> {experience.id}"
        )

  