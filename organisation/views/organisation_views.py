# organisation_views.py
from rest_framework.response import Response
from ..models import Organisation
from ..serializers import OrganisationSerializer
from django.core.exceptions import PermissionDenied
from .base_view import BaseCRUDView
from rest_framework import status
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated

class OrganisationCRUDView(BaseCRUDView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganisationSerializer
    queryset = Organisation.objects.all()

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_superuser:
            return queryset
    
        if self.request.user.is_superuser:
            return super().get_queryset()

        if hasattr(user, 'employee_profile') and user.employee_profile.branch:
            return queryset.filter(id=user.employee_profile.branch.organisation.id)
            
        return self.queryset.none() 

    def perform_create(self, serializer):
        if self.request.user.is_superuser or (
            hasattr(self.request.user, 'employee_profile') and 
            self.request.user.employee_profile.is_branch_admin):
            serializer.save(created_by=self.request.user, modified_by=self.request.user)
        else:
            raise PermissionDenied("Only superusers or branch admins can create organisations")

    def perform_update(self, serializer):
        if self.request.user.is_superuser:
            serializer.save(modified_by=self.request.user)
            return
        else:
            raise PermissionDenied("Only superusers can update organisations")

    def perform_destroy(self, instance):
        if self.request.user.is_superuser:
            return super().perform_destroy(instance)
        else:
            raise PermissionDenied("Only superusers can delete organisations")

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAuthenticated()]