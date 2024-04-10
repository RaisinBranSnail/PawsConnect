import logging
import signal

from allauth.account.signals import user_signed_up
from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.sessions.models import Session
from django.db.models.signals import post_save
from django.dispatch import receiver
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import GoogleV3

from .models import CustomUser  # Ensure this matches your user model import

# Setup logger
logger = logging.getLogger(__name__)


# Geocode user location on user model update
@receiver(post_save, sender=CustomUser)
def geocode_user_location(sender, instance=None, created=False, **kwargs):
    if instance and created and not instance.location and instance.city and instance.state and instance.zip_code:
        try:
            geolocator = GoogleV3(api_key=settings.GOOGLE_MAPS_API_KEY)
            address = f"{instance.city}, {instance.state}, {instance.zip_code}"
            location = geolocator.geocode(address)

            if location:
                # Create a Point object from latitude and longitude
                instance.location = Point(location.longitude, location.latitude)
                # Update the instance without triggering a loop
                CustomUser.objects.filter(pk=instance.pk).update(location=instance.location)
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            logger.warning(f"Geocoding error for user {instance.pk}: {e}")


# Clear all sessions on shutdown
def clear_sessions_on_shutdown(signum, frame):
    logger.info("Received SIGTERM signal. Clearing all sessions...")
    Session.objects.all().delete()


# Connect the SIGTERM signal to the clear_sessions_on_shutdown function
# This could be placed within an AppConfig.ready() method, or similarly, here for simplicity
signal.signal(signal.SIGTERM, clear_sessions_on_shutdown)


# Optional: YourAppConfig ready method if you're using AppConfig to connect signals

@receiver(user_signed_up)
def mark_profile_incomplete(sender, **kwargs):
    user = kwargs.pop('user')
    # Assuming you have a field or a related model to track profile completeness
    user.profile_incomplete = True
    user.save()