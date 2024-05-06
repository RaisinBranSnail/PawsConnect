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
    path('transfer_requests/', views.view_transfer_requests, name='view_transfer_requests'),
    path('accept_transfer/<int:pk>/', views.accept_transfer_request, name='accept_transfer_request'),
    path('reject_transfer/<int:pk>/', views.reject_transfer_request, name='reject_transfer_request'),

    path('', include(router.urls)),
]
