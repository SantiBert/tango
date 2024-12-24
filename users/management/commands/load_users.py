from django.core.management.base import BaseCommand
from rest_framework_simplejwt.tokens import RefreshToken

from pjbackend.constants import LIST_DEFAULT_USERS
from users.models import CustomUser

class Command(BaseCommand):
    help = 'Create some users for testing environment'
    def handle(self, *args, **options):
        for user_data in LIST_DEFAULT_USERS:
            password = user_data.pop('password')
            username = user_data.pop('username')
            user, created = CustomUser.objects.get_or_create(
              username=username, 
              defaults=user_data
            )
            if created:
              user.set_password(password)
              user.is_registered = True
              user.save()
              self._create_token(user)
              self.stdout.write(self.style.SUCCESS(f'User "{user.email}" created successfully'))
            else:
              self.stdout.write(self.style.WARNING(f'The user "{username}" already exists. No new user was created.'))
    
    def _create_token(self, user):
        RefreshToken.for_user(user)
