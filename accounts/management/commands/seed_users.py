from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Create initial test users'

    def handle(self, *args, **options):
        users_data = [
            {
                'first_name': 'سارا',
                'last_name': 'احمدی',
                'email': 'sara@gmail.com',
                'password': 'SaraPass@123',
                'phone_number': '09122222222'
            },
            {
                'first_name': 'علی',
                'last_name': 'رضایی',
                'email': 'ali@gmail.com',
                'password': 'AliPass@123',
                'phone_number': '09123333333'
            },
            {
                'first_name': 'مریم',
                'last_name': 'حسینی',
                'email': 'maryam@gmail.com',
                'password': 'MaryamPass@123',
                'phone_number': '09124444444'
            }
        ]

        for u in users_data:
            if not User.objects.filter(email=u['email']).exists():
                User.objects.create_user(**u)
                self.stdout.write(self.style.SUCCESS(f"User created: {u['email']}"))
            else:
                self.stdout.write(self.style.WARNING(f"User already exists: {u['email']}"))
