import logging
from django.db import IntegrityError
from django.urls import reverse
from allauth.account.views import LogoutView
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from rest_framework import viewsets, status, serializers
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import login
from Content.models import Post
from PetManagement.models import Pet, PetProfile
from .decorators import profile_completion_required
from .forms import CustomLoginForm, EditProfileForm, UserCompletionForm, PetFormSet, SearchForm, UserRegistrationForm, \
    PetForm
from .models import CustomUser, Photo, Friendship
from .serializers import CustomUserSerializer, FriendshipSerializer
from .utils import search_pets, search_users
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from .models import CustomUser
from PetManagement.models import Pet  # Adjust this import according to the actual location of the Pet model.
from UserManagement.models import CustomUser, UserProfile
from .models import Post
from .forms import PostForm
from django.contrib import messages
from django import template


register = template.Library()

User = get_user_model()

logger = logging.getLogger(__name__)


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()



def user_login(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                # Correctly form the redirect URL
                redirect_url = reverse('UserManagement:user_completion') if user.profile_incomplete else reverse('UserManagement:profile', kwargs={'slug': user.slug})
                return redirect(redirect_url)  # Use Django's redirect function
            else:
                return JsonResponse({'error': "Invalid username or password"}, status=400)
        return render(request, 'UserManagement/login.html', {'form': form})
    else:
        form = CustomLoginForm()
        return render(request, 'UserManagement/login.html', {'form': form})

def home(request):
    if request.user.is_authenticated:
        return redirect('UserManagement:profile', slug=request.user.slug)
    else:
        return render(request, 'UserManagement/home.html')


from django.contrib.auth import login, authenticate

def register(request):
    user_form = UserRegistrationForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and user_form.is_valid():
        user = user_form.save(commit=False)
        user.save()
        user.backend = 'django.contrib.auth.backends.ModelBackend'  # Specify the backend
        login(request, user)  # Log the user in immediately after registration



        return redirect('UserManagement:profile', slug=user.slug)  # Redirect to the user's profile

    return render(request, 'UserManagement/register.html', {
        'user_form': user_form,
    })



@login_required
def add_pet(request):
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            pet.save()

            # Save the profile picture to the pet's profile
            profile_picture = form.cleaned_data.get('profile_picture')
            pet_profile, created = PetProfile.objects.get_or_create(pet=pet)
            pet_profile.profile_picture = profile_picture
            pet_profile.save()

            return redirect('UserManagement:pets')  # Redirect to the pets page
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = PetForm()
        return render(request, 'UserManagement/add_pet.html', {'form': form})

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('UserManagement:login')

    def dispatch(self, request, *args, **kwargs):
        logger.info(f"CustomLogoutView: Logging out user: {request.user}")
        response = super().dispatch(request, *args, **kwargs)
        logger.info("CustomLogoutView: User logged out.")
        return response
@login_required
@profile_completion_required
def profile(request, slug):
    user = get_object_or_404(CustomUser, slug=slug)
    followers_count = user.followers.count()  # Fetches the number of followers
    posts = Post.objects.filter(user=user)
    show_friend_request_button = user.is_private and not request.user in user.followers.all()
    followers = user.followers.all()
    following_users = user.followed_users.all().count()  # count of followed users

    followed_pets_count = user.followed_pets.count()  # count of followed pets

    has_pending_request = Friendship.objects.filter(user_from=user, user_to=request.user, status='pending').exists()
    total_following = following_users + followed_pets_count  # Total count of following users and pets

    pet_data = []
    for pet in user.pets.all():
        pet_info = {
            'profile_picture_url': pet.profile.profile_picture.url if pet.profile.profile_picture else None,
            'profile_url': reverse('PetManagement:pet_profile', kwargs={'slug': pet.slug}),
            'name': pet.name,
            'age': pet.age,
            'breed': pet.breed,
            'about_me': pet.profile.description,
        }
        pet_data.append(pet_info)

    context = {
        'user': user,
        'posts': posts,
        'has_pending_request': has_pending_request,
        'show_friend_request_button': show_friend_request_button,
        'pet_data': pet_data,
        'total_following': total_following,  # Combined total following count
        'is_following': user in request.user.followed_users.all(),
        'followers': followers,  # Using .count() to just send the number
        'followers_count': followers_count,
        'following': following_users,  # Just the count of following users

        'followed_pets_count': followed_pets_count,  # Count of followed pets

    }

    return render(request, 'UserManagement/profile.html', context)
@login_required
def edit_profile(request, slug):
    user = get_object_or_404(CustomUser, slug=slug)
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('UserManagement:profile', slug=user.slug)
        else:
            print(form.errors)  # Print form errors to the console or handle them
    else:
        form = EditProfileForm(instance=user)

    return render(request, 'UserManagement/edit_profile.html', {
        'form': form,
        'user': user  # Pass user to the template for context
    })

@login_required
def edit_pet_profile(request, pet_slug):
    pet = get_object_or_404(Pet, slug=pet_slug, owner=request.user)
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            form.save()
            return redirect('UserManagement:pets')
    else:
        form = PetForm(instance=pet)
    return render(request, 'UserManagement/edit_pet_profile.html', {'form': form, 'pet': pet})

@login_required
def user_completion(request):
    if request.method == 'POST':
        form = UserCompletionForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('UserManagement:profile', slug=request.user.slug)
    else:
        form = UserCompletionForm(instance=request.user)
    return render(request, 'UserManagement/user_completion.html', {'form': form})


def search(request):
    form = SearchForm(request.GET or None)
    context = {
        'form': form,
        'search_type': None,
        'results': None,
    }
    if form.is_valid():
        search_type = form.cleaned_data['type']
        context['search_type'] = search_type
        if search_type == 'user':
            users = search_users(
                query=form.cleaned_data['query'],
                location_point=form.cleaned_data.get('location_point', None),
                search_range=form.cleaned_data.get('range', None)
            )
            context['results'] = users
        elif search_type == 'pet':
            pets = search_pets(
                pet_id=form.cleaned_data.get('pet_id', None),
                name=form.cleaned_data.get('pet_name', None)
            )
            context['results'] = pets
    return render(request, 'UserManagement/search.html', context)


@login_required
def photos(request):
    user_photos = Photo.objects.filter(user=request.user)
    return render(request, 'UserManagement/photos.html', {'user_photos': user_photos})


@login_required
def friends(request):
    user_friends = request.user.profile.friends.all()
    return render(request, 'UserManagement/friends.html', {'user_friends': user_friends})


@login_required
def pets(request):
    user_pets = Pet.objects.filter(owner=request.user)
    return render(request, 'UserManagement/pets.html', {'user_pets': user_pets})


class FriendshipViewSet(viewsets.ModelViewSet):
    queryset = Friendship.objects.all()
    serializer_class = FriendshipSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user_from = self.request.user
        user_to = serializer.validated_data.get('user_to')
        if user_from == user_to:
            raise serializers.ValidationError("You cannot send a friendship request to yourself.")
        if Friendship.objects.filter(user_from=user_from, user_to=user_to).exists():
            raise serializers.ValidationError('A friendship request already exists between these users.')
        serializer.save(user_from=user_from)

    @action(detail=True, methods=['post'], name='Accept Friendship')
    def accept(self, request, pk=None):
        friendship = self.get_object()
        if friendship.user_to == request.user and friendship.status == 'pending':
            friendship.status = 'accepted'
            friendship.save(update_fields=['status'])
            return Response({'status': 'accepted'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Unauthorized or invalid state'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], name='Reject Friendship')
    def reject(self, request, pk=None):
        friendship = self.get_object()
        if friendship.user_to == request.user and friendship.status == 'pending':
            friendship.status = 'rejected'
            friendship.save(update_fields=['status'])
            return Response({'status': 'rejected'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Unauthorized or invalid state'}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        friendship = self.get_object()
        if friendship.user_from == request.user or friendship.user_to == request.user:
            return super().destroy(request, *args, **kwargs)
        else:
            return Response({'error': 'You do not have permission to delete this friendship.'},
                            status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        friendship = self.get_object()
        if not (friendship.user_from == request.user or friendship.user_to == request.user):
            return Response({'error': 'You do not have permission to modify this friendship.'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)



@login_required
def delete_pet(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)

    if request.method == 'POST':
        pet.delete()
        return redirect('UserManagement:pets')
    else:
        return render(request, 'UserManagement/delete_pet.html', {'pet': pet})


@login_required
def search_profile(request):
    username = request.GET.get('username', None)
    if username:
        try:
            user = User.objects.get(username=username)
            return JsonResponse({
                'success': True,
                'user_id': user.id,
                'username': user.username,
                'profile_info': user.profile.about_me  # Corrected to use 'about_me'
            })
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
    return JsonResponse({'success': False, 'message': 'No username provided'}, status=400)
@login_required
def transfer_pet(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        form = TransferPetForm(request.POST)
        if form.is_valid():
            transfer_request = form.save(commit=False)
            transfer_request.pet = pet
            transfer_request.from_user = request.user
            # Setting the to_user from the form
            transfer_request.to_user = form.cleaned_data['to_user']
            transfer_request.save()
            # Updating the pet's owner
            pet.owner = transfer_request.to_user
            pet.save()
            return redirect('UserManagement:pets')
    else:
        form = TransferPetForm()

    return render(request, 'UserManagement/transfer_pet.html', {'form': form, 'pet': pet})


def search(request):
    query = request.GET.get('query', '')
    if query:
        user_results = CustomUser.objects.filter(username__icontains=query)
        pet_results = Pet.objects.filter(name__icontains=query)
    else:
        user_results = Pet.objects.none()
        pet_results = CustomUser.objects.none()

    context = {
        'user_results': user_results,
        'pet_results': pet_results,
        'query': query
    }
    return render(request, 'UserManagement/search_results.html', context)


@login_required
def send_friend_request(request, user_id):
    target_user = get_object_or_404(CustomUser, pk=user_id)
    if request.user == target_user:
        return JsonResponse({'error': 'Cannot send friend request to yourself'}, status=400)

    # Check if the friendship already exists
    if Friendship.objects.filter(user_from=request.user, user_to=target_user).exists():
        return JsonResponse({'error': 'Friend request already sent'}, status=400)

    # Since the friendship doesn't exist, create it
    Friendship.objects.create(user_from=request.user, user_to=target_user)
    return JsonResponse({'success': True}, status=200)

@login_required
def friend_requests(request, slug):
    user = get_object_or_404(CustomUser, slug=slug)
    incoming_requests = Friendship.objects.filter(user_to=user, status='pending')
    context = {
        'incoming_requests': incoming_requests,
        'user': user,
    }
    return render(request, 'UserManagement/friend_requests.html', context)


def has_pending_request_from(user, other_user):
    return Friendship.objects.filter(user_from=other_user, user_to=user, status='pending').exists()



@login_required
def accept_friend_request(request, request_id):
    friendship = get_object_or_404(Friendship, id=request_id, user_to=request.user, status='pending')
    friendship.status = 'accepted'
    friendship.save()
    return redirect('UserManagement:friend_requests', slug=request.user.slug)

@login_required
def reject_friend_request(request, request_id):
    friendship = get_object_or_404(Friendship, id=request_id, user_to=request.user, status='pending')
    friendship.status = 'declined'
    friendship.delete()  # or change status to 'declined' based on your model design
    return redirect('UserManagement:friend_requests', slug=request.user.slug)
# Follow/following functionality


from django.views.decorators.csrf import csrf_exempt


# views.py
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

@login_required
def follow_pet(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    if request.user in pet.followers.all():
        pet.followers.remove(request.user)
    else:
        pet.followers.add(request.user)
    return redirect('UserManagement:user_pets', slug=pet.owner.slug)


@login_required
def followers_list(request, slug):
    # Fetch user by slug, not by id
    user = get_object_or_404(CustomUser, slug=slug)
    followers = user.followers.all()  # Ensure 'followers' is correctly set up in your model
    return render(request, 'UserManagement/followers_list.html', {'user': user, 'followers': followers})

@login_required
def following_list(request, slug):
    user = get_object_or_404(CustomUser, slug=slug)
    following_users = user.followed_users.all()
    following_pets = user.followed_pets.all()

    context = {
        'user': user,
        'following_users': following_users,
        'following_pets': following_pets
    }
    return render(request, 'UserManagement/following_list.html', context)

def friendship_status(request):
    if request.user.is_authenticated:
        # Example: You can modify according to actual use case
        pending_requests = Friendship.objects.filter(user_to=request.user, status='pending').count()
        return {
            'pending_friend_requests_count': pending_requests,
        }
    return {}





@login_required
def follow_user(request, user_id):
    target_user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        if target_user != request.user:
            if target_user not in request.user.followed_users.all():
                request.user.followed_users.add(target_user)
            else:
                request.user.followed_users.remove(target_user)
        # Redirect back to the same page
        return redirect(request.META.get('HTTP_REFERER', 'default_fallback_view_name'))
    return redirect('UserManagement:profile', slug=request.user.slug)
@login_required
def unfollow_user(request, user_id):
    target_user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        if target_user in request.user.followed_users.all():
            request.user.followed_users.remove(target_user)
        # Redirect back to the same page
        return redirect(request.META.get('HTTP_REFERER', 'default_fallback_view_name'))
    return redirect('UserManagement:profile', slug=request.user.slug)


@login_required
def unfollow_pet(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    user = request.user
    if pet in user.followed_pets.all():
        user.followed_pets.remove(pet)
    return redirect('UserManagement:profile', slug=user.slug)

@login_required
def edit_profile(request, slug):
    user = get_object_or_404(CustomUser, slug=slug)
    if user != request.user:
        return redirect('UserManagement:profile', slug=user.slug)
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('UserManagement:profile', slug=user.slug)
    else:
        form = EditProfileForm(instance=user)
    return render(request, 'UserManagement/edit_profile.html', {'form': form, 'user': user})



@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            form.save_m2m()  # This is required to save the many-to-many relationships.
            return redirect('UserManagement:profile', slug=request.user.slug)
    else:
        form = PostForm(user=request.user)

    return render(request, 'UserManagement/create_post.html', {'form': form})

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('UserManagement:profile', slug=request.user.slug)
    else:
        form = PostForm(instance=post, user=request.user)

    return render(request, 'UserManagement/edit_post.html', {'form': form, 'post': post})

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    if request.method == 'POST':
        post.delete()
        return redirect('UserManagement:profile', slug=request.user.slug)

    return render(request, 'UserManagement/delete_post.html', {'post': post})

@login_required
def post_feed(request):
    posts = Post.objects.exclude(user=request.user)
    return render(request, 'UserManagement/post_feed.html', {'posts': posts})

def user_pets(request, slug):
    user = get_object_or_404(User, slug=slug)
    user_pets = Pet.objects.filter(owner=user)  # Assuming Pet model has an 'owner' field linked to User
    return render(request, 'UserManagement/pets.html', {'user_pets': user_pets, 'user': user})