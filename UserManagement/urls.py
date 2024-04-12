# UserManagement/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from .views import CustomLogoutView
from .views import add_pet, delete_pet

app_name = 'UserManagement'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', CustomLogoutView.as_view(next_page='UserManagement:login'), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/<slug:slug>/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('friends/', views.friends, name='friends'),
    path('photos/', views.photos, name='photos'),
    path('pets/', views.pets, name='pets'),
    path('search/', views.search, name='search'),
    path('complete/', views.user_completion, name='user_completion'),
    path('add_pet/', add_pet, name='add_pet'),
    path('delete_pet/', delete_pet, name='delete_pet'),
    path('edit_pet/<slug:pet_slug>/', views.edit_pet_profile, name='edit_pet_profile'),
]
