from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from userprofile.models import UserProfile

class Command(BaseCommand):
    help = 'Create missing UserProfile for existing Users'

    def handle(self, *args, **options):
        users = User.objects.all()
        for user in users:
            try:
                user.profile
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(user=user)
                self.stdout.write(f'Created profile for user: {user.username}')
        self.stdout.write(self.style.SUCCESS('Finished creating profiles for all users'))