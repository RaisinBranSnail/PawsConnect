from autoslug import AutoSlugField
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser

from UserManagement.models import CustomUser


class PetManager(models.Manager):
    def search(self, pet_id=None, name=None):
        queryset = self.get_queryset()
        if pet_id:
            queryset = queryset.filter(id=pet_id)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class Pet(models.Model):
    class PetType(models.TextChoices):
        DOG = 'dog', 'Dog'
        CAT = 'cat', 'Cat'
        BIRD = 'bird', 'Bird'
        REPTILE = 'reptile', 'Reptile'
        OTHER = 'other', 'Other'

    owner = models.ForeignKey(
        'UserManagement.CustomUser',
        on_delete=models.CASCADE,
        related_name='owned_pets',  # Unique related_name for reverse relationship
        help_text="The user who owns the pet."
    )
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    age = models.PositiveIntegerField(blank=True)
    pet_type = models.CharField(max_length=20, choices=PetType.choices, default=PetType.OTHER)
    slug = AutoSlugField(populate_from='name', unique=True, always_update=True)

    def save(self, *args, **kwargs):
        self.pet_type = self.pet_type.lower()  # Ensure pet_type is always stored in lowercase
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('PetManagement:pet_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name

    def get_display_pet_type(self):
        """Returns a nicely formatted pet type for display."""
        return self.pet_type.capitalize()

class PetProfile(models.Model):
    pet = models.OneToOneField(Pet, on_delete=models.CASCADE, related_name='profile')
    description = models.TextField(blank=True, max_length=500, default='Enter text here...')
    profile_picture = models.ImageField(upload_to='pet_profile_pics/', null=True, blank=True)

    # Add any other fields specific to the pet profile

    def __str__(self):
        return f"{self.pet.name}'s Profile"


def pet_photo_path(instance, filename):
    # This function generates a unique file path for each photo
    return f'pet_photos/{instance.pet.slug}/{filename}'


class PetPhoto(models.Model):
    pet = models.ForeignKey(Pet, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=pet_photo_path)
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # You could add more detail here if needed, like the upload date
        return f"Photo of {self.pet.name} uploaded on {self.uploaded_at.strftime('%Y-%m-%d')}"


class PetTransferRequest(models.Model):
    class TransferStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        CANCELED = 'canceled', 'Canceled'

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='transfer_requests')
    from_user = models.ForeignKey('UserManagement.CustomUser', related_name='sent_transfers', on_delete=models.CASCADE)
    to_user = models.ForeignKey('UserManagement.CustomUser', related_name='received_transfers',
                                on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=TransferStatus.choices, default=TransferStatus.PENDING)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transfer of {self.pet.name} from {self.from_user.username} to {self.to_user.username}"
