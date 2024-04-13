from django.db import transaction
from PetManagement.forms import PetForm


# UserManagement/utils.py


@transaction.atomic
def create_user(cls, username, email, password, num_pets, pet_form_data):
    user = cls.objects.create_user(username=username, email=email, password=password)

    # Create pets
    for i in range(num_pets):
        pet_form = PetForm(pet_form_data[i], prefix=str(i))
        if pet_form.is_valid():
            pet = pet_form.save(commit=False)
            pet.owner = user
            pet.save()

    # Set profile completeness
    user.set_profile_incomplete()

    return user, True


from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import Q
from .models import CustomUser  # Assuming CustomUser is in the same app


def search_users(query=None, location_point=None, search_range=None):
    queryset = CustomUser.objects.all()
    if query:
        queryset = queryset.filter(
            Q(username__icontains=query) | Q(display_name__icontains=query)
        )
    if location_point and search_range:
        search_distance = D(mi=search_range)
        queryset = queryset.annotate(
            distance=Distance('location', location_point)
        ).filter(location__distance_lte=(location_point, search_distance))
    return queryset
