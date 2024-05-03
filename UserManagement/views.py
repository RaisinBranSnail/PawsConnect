import logging

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
    pet_formset = PetFormSet(request.POST or None, request.FILES or None, instance=None)

    if request.method == 'POST' and user_form.is_valid():
        user = user_form.save(commit=False)
        user.save()
        user.backend = 'django.contrib.auth.backends.ModelBackend'  # Specify the backend
        login(request, user)  # Log the user in immediately after registration

        if pet_formset.is_bound and pet_formset.is_valid():
            pet_formset.instance = user
            pet_formset.save()

        return redirect('UserManagement:profile', slug=user.slug)  # Redirect to the user's profile

    return render(request, 'UserManagement/register.html', {
        'user_form': user_form,
        'pet_formset': pet_formset
    })



@login_required
def add_pet(request):
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            pet.save()
            PetProfile.objects.create(pet=pet)
            return JsonResponse({'success': True, 'message': f'{pet.name} successfully added.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=405)


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
    print("User Bio:", user.about_me)  # This will print the bio in the console
    print("Debug: User slug is", user.slug)  # Ensure this prints the correct slug
    posts = Post.objects.filter(user=user)

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
        'pet_data': pet_data,
    }
    print("User slug:", user.slug)  # Debugging statement to check the slug value
    print(user.slug)  # Add this line to check what the slug is right before rendering
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
def delete_pet(request):
    if request.method == 'POST' and 'pet_id' in request.POST:
        try:
            pet = Pet.objects.get(id=request.POST['pet_id'], owner=request.user)
            pet.delete()
            return JsonResponse({'success': True, 'message': 'Pet successfully deleted.'})
        except Pet.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Pet not found'}, status=404)
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=405)
