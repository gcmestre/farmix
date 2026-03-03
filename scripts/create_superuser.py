"""
Create a superuser and admin profile for initial setup.
Run with: python manage.py shell < scripts/create_superuser.py
"""

import os

from django.contrib.auth.models import User

from apps.core.models import UserProfile

email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@compoundmeds.local")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin123")

if not User.objects.filter(email=email).exists():
    user = User.objects.create_superuser(username=email, email=email, password=password)
    UserProfile.objects.create(user=user, role=UserProfile.Role.ADMIN)
    print(f"Superuser '{email}' created with admin profile.")
else:
    print(f"Superuser '{email}' already exists.")
