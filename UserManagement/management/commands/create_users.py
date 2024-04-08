import json
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from faker import Faker
from pathlib import Path

class Command(BaseCommand):
    help = 'Creates dummy users from an Excel file'

    def handle(self, *args, **kwargs):
        from UserManagement.forms import UserRegistrationForm

        # Define the path to the Excel file
        excel_file_path = Path(settings.BASE_DIR) / 'misc' / 'DummyData.xlsx'

        # Load the Excel file
        df = pd.read_excel(excel_file_path, header=1)

        fake = Faker()
        for _ in range(250):  # Adjust the range as needed
            row = df.sample(n=1).iloc[0]
            user_data = {
                'username': fake.user_name(),
                'email': fake.email(),
                'password1': 'TempPass!234',
                'password2': 'TempPass!234',
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'city': row['City'],
                'state': row['State'],
                'zip_code': str(row['Zip']),
                'preferred_language': 'en',
                'display_name': fake.user_name(),  # Updated to use Faker
                # Removed 'profile_picture': None, if not handling file uploads
                'has_pets': fake.boolean(),  # Randomly decide if the user has pets
                'about_me': 'This is an autogenerated user.',
            }

            form = UserRegistrationForm(data=user_data)

            if form.is_valid():
                form.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully created user {user_data['first_name']} {user_data['last_name']}."))
            else:
                # Enhanced error logging
                errors = json.dumps(form.errors.get_json_data(), indent=4)
                self.stdout.write(self.style.ERROR(
                    f"Failed to create user {user_data['first_name']} {user_data['last_name']}: {errors}"))