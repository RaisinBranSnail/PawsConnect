from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PetViewSet, PetTransferRequestViewSet
from . import views
router = DefaultRouter()
router.register(r'pets', PetViewSet)
router.register(r'transfer_requests', PetTransferRequestViewSet)
app_name = 'PetManagement'

urlpatterns = [
    path('transfer_pet/<int:pet_id>/', views.transfer_pet, name='transfer_pet'),
    path('profile/<slug:slug>/', views.pet_profile, name='pet_profile'),

    path('', include(router.urls)),
]
