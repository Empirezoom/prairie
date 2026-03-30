import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prairiewealth_project.settings')
django.setup()

from django.contrib.auth.models import User
from bankapp.models import UserProfile

for user in User.objects.all():
    profile, created = UserProfile.objects.get_or_create(user=user)
    if created:
        print(f"Created profile for {user.username}")
    else:
        print(f"Profile exists for {user.username}")
