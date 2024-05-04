from django.db import transaction
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from django.contrib import messages
from django.http import JsonResponse
from UserManagement.models import CustomUser
from .models import Pet, PetTransferRequest
from .permissions import IsOwnerPermission, IsOwnerOrRecipient
from .serializers import PetSerializer, PetTransferRequestSerializer, PetTransferRequestDetailSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Pet, PetTransferRequest
from .forms import TransferPetForm
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from UserManagement.models import CustomUser
class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerPermission]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """ Custom implementation to delete a pet only if certain conditions are met. """
        instance = self.get_object()
        if not request.user == instance.owner:
            return Response({"detail": "You do not have permission to delete this pet."},
                            status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        return Pet.objects.filter(owner=self.request.user)


class PetTransferRequestViewSet(viewsets.ModelViewSet):
    queryset = PetTransferRequest.objects.all()
    serializer_class = PetTransferRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrRecipient]

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        transfer_request = self.get_object()
        if transfer_request.to_user != request.user:
            return Response({'error': 'You are not authorized to accept this transfer request.'}, status=status.HTTP_403_FORBIDDEN)
        if transfer_request.status != PetTransferRequest.TransferStatus.PENDING:
            return Response({'error': 'Transfer request is not pending.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            pet = transfer_request.pet
            pet.owner = transfer_request.to_user
            pet.save()

            transfer_request.from_user.pets.remove(pet)
            transfer_request.to_user.pets.add(pet)

            transfer_request.status = PetTransferRequest.TransferStatus.APPROVED
            transfer_request.save()

        return Response({'message': 'Pet transfer successful.'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        transfer_request = self.get_object()
        if transfer_request.to_user != request.user:
            return Response({'error': 'You are not authorized to reject this transfer request.'}, status=status.HTTP_403_FORBIDDEN)
        if transfer_request.status != PetTransferRequest.TransferStatus.PENDING:
            return Response({'error': 'Transfer request is not pending.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            transfer_request.status = PetTransferRequest.TransferStatus.REJECTED
            transfer_request.save()

        return Response({'message': 'Pet transfer rejected.'})




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



@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(CustomUser, id=user_id)
    user_profile = request.user.profile

    if user_to_follow in user_profile.friends.all():
        user_profile.friends.remove(user_to_follow)
        is_following = False
    else:
        user_profile.friends.add(user_to_follow)
        is_following = True

    return JsonResponse({"is_following": is_following})
# @login_required
# def follow_pet(request, pet_id):
#     pet = Pet.objects.get(pk=pet_id)
#     request.user.followed_pets.add(pet)
#     return redirect('UserManagement:search')  # Redirect to the search page or wherever appropriate