from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import CustomLogoutView, add_pet, delete_pet, edit_pet_profile
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet
from .views import search_profile
router = DefaultRouter()
router.register('users', CustomUserViewSet)
router.register(r'friendships', views.FriendshipViewSet, basename='friendship')
app_name = 'UserManagement'

urlpatterns = [
    path('', include(router.urls)),
    path('home/', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', CustomLogoutView.as_view(next_page='UserManagement:login'), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/<slug:slug>/', views.profile, name='profile'),
    path('edit_profile/<slug:slug>/', views.edit_profile, name='edit_profile'),
    path('friends/', views.friends, name='friends'),
    path('photos/', views.photos, name='photos'),
    path('pets/', views.pets, name='pets'),
    path('search/', views.search, name='search'),
    path('complete/', views.user_completion, name='user_completion'),
    path('add_pet/', add_pet, name='add_pet'),
    path('delete_pet/<int:pet_id>/', views.delete_pet, name='delete_pet'),
    path('edit_pet_profile/<slug:pet_slug>/', views.edit_pet_profile, name='edit_pet_profile'),
    path('pet_management/', include('PetManagement.urls')),  # Include PetManagement URLs
    path('search_profile/', views.search_profile, name='search_profile'),
    path('search/', views.search, name='search'),
    path('follow_user/<int:user_id>/', views.follow_user, name='follow_user'),
    path('follow_pet/<int:pet_id>/', views.follow_pet, name='follow_pet'),
    path('followers/<int:user_id>/', views.followers_list, name='followers_list'),
    path('user/following_list/<slug:slug>/', views.following_list, name='following_list'),
    path('unfollow_user/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path('pets/', include('PetManagement.urls', namespace='PetManagement')),
    path('create-post/', views.create_post, name='create_post'),
    path('edit-post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('post-feed/', views.post_feed, name='post_feed'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
