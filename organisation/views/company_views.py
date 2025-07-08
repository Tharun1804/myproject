# company_views.py
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from organisation.models import Company
from organisation.serializers import CompanySerializer
from .base_view import BaseCRUDView

class CompanyCRUDView(BaseCRUDView):
    serializer_class = CompanySerializer
    queryset = Company.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_superuser:
            return queryset
            
        if hasattr(user, 'employee_profile'):
            employee = user.employee_profile
            if employee.branch:
                # Return only the company for the user's branch
                return queryset.filter(branch=employee.branch)
                
        return queryset.none()

    def perform_create(self, serializer):
        branch = serializer.validated_data.get('branch')
        # Ensure only one company per branch
        if Company.objects.filter(branch=branch).exists():
            raise ValidationError("A company already exists for this branch")
        
        if self.request.user.is_superuser:
            serializer.save(created_by=self.request.user, modified_by=self.request.user)
            return
            
        user = self.request.user
        if not user.is_superuser:
            if hasattr(user, 'employee_profile'):
                if branch != user.employee_profile.branch:
                    raise PermissionDenied("You can only create a company for your own branch")
        
        if user.is_superuser:
            serializer.save(created_by=user, modified_by=user)
            return
        if hasattr(user, 'employee_profile'):
            employee = user.employee_profile
            if employee.branch:
                # Automatically assign the company to the user's branch
                serializer.save(
                    branch=employee.branch,
                    created_by=user,
                    modified_by=user
                )
                return
            
        raise PermissionDenied("You don't have permission to create companies")

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        
        if user.is_superuser:
            serializer.save(modified_by=user)
            return
        
        if hasattr(user, 'employee_profile'):
            if instance.branch != user.employee_profile.branch:
                raise PermissionDenied("You can only update your branch's company")
            
            # Ensure the updated branch is the same as the admin's branch
            branch = serializer.validated_data.get('branch')
            if branch and branch != user.employee_profile.branch:
                raise PermissionDenied("You can only assign your branch")
                
            serializer.save(modified_by=user)
        else:
            raise PermissionDenied("You don't have permission to update companies")
        
        
    def perform_destroy(self, instance):
        user = self.request.user
        if self.request.user.is_superuser or self.request.user.is_branch_admin:
            return super().perform_destroy(instance)
        if not self.request.user.is_superuser:
            raise PermissionDenied("Only superusers can delete companies")
        return super().perform_destroy(instance)


