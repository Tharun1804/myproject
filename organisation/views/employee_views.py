from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from ..models import Employee
from ..serializers import EmployeeSerializer
from .base_view import BaseCRUDView
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from organisation import models


from .permissions import (
    IsBranchAdmin, 
    IsEmployeeReadOnly,
    CanCreateEmployee,
    CanEditEmployee,
    CanDeleteEmployee
)
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class EmployeeCRUDView(BaseCRUDView):
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()
    

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated(), IsEmployeeReadOnly()]
        elif self.request.method == 'POST':
            return [IsAuthenticated(), CanCreateEmployee()]
        elif self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated(), CanEditEmployee()]
        elif self.request.method == 'DELETE':
            return [IsAuthenticated(), CanDeleteEmployee()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_superuser:
            return queryset

        if hasattr(user, 'employee_profile'):
            employee = user.employee_profile
            if employee.branch:
                return queryset.filter(branch=employee.branch)

        return queryset.filter(user=user)

    
    def perform_create(self, serializer):
        user = self.request.user
        validated_data = serializer.validated_data

        if not user.is_superuser:
            if 'is_branch_admin' in validated_data:
                validated_data.pop('is_branch_admin')
            if 'can_create' in validated_data:
                validated_data.pop('can_create')
            if 'can_edit' in validated_data:
                validated_data.pop('can_edit')
            if 'can_delete' in validated_data:
                validated_data.pop('can_delete')
        
        # Extract password and user data
        password = validated_data.pop('password', None)
        email = validated_data.pop('email', None)  # Get email from validated_data
        name = validated_data.pop('name', None)
        is_superuser = validated_data.pop('is_superuser', False)
        is_branch_admin = validated_data.pop('is_branch_admin', False)
        
        
        if not password:
            raise ValidationError({"password": "This field is required when creating an employee"})
        if not email:
            raise ValidationError({"email": "This field is required when creating an employee"})
        if not name:
            raise ValidationError({"name": "This field is required when creating an employee"})

        # Create the user first
        user_instance = User.objects.create_user(
            email=email,
            name=name,
            password=password,
            is_active=True,
            is_superuser=is_superuser,
        )

        if user.is_superuser:
            employee = serializer.save(
                user=user_instance,
                created_by=user,
                modified_by=user, 
                is_superuser=is_superuser,
                is_branch_admin=is_branch_admin,
            )
            return
        # Add permission fields handling
        

        elif hasattr(user, 'employee_profile'):
            employee = user.employee_profile
            if employee.can_create and employee.branch:
                serializer.save(
                    user=user_instance,
                    branch=employee.branch,
                    company=employee.branch.company,
                    created_by=user,
                    modified_by=user,
                    is_branch_admin=False,
                    is_superuser=False,
                    can_create=False,
                    can_edit=False,
                    can_delete=False
                )
                return

        raise PermissionDenied("You don't have permission to create employees")


    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        
        if not instance.user:
            raise ValidationError("Employee record has no associated user")
        
        if user.is_superuser:
            # Superusers can update anything, including is_superuser flag
            is_superuser = serializer.validated_data.get('is_superuser', instance.is_superuser)
            is_branch_admin = serializer.validated_data.get('is_branch_admin', instance.is_branch_admin)
            can_create = serializer.validated_data.get('can_create', instance.can_create)
            can_edit = serializer.validated_data.get('can_edit', instance.can_edit)
            can_delete = serializer.validated_data.get('can_delete', instance.can_delete)

            if not is_branch_admin and instance.is_branch_admin:
                instance.is_branch_admin = False


            instance.can_create = can_create
            instance.can_edit = can_edit
            instance.can_delete = can_delete

            if instance.is_superuser:
                raise PermissionDenied("Cannot modify other superusers")
            
            # Update user's superuser status if changed
            if instance.user.is_superuser != is_superuser:
                instance.user.is_superuser = is_superuser
                instance.user.save()
                
            if instance.is_branch_admin != is_branch_admin:
                instance.is_branch_admin = is_branch_admin
            
            serializer.save(modified_by=user)

        elif hasattr(user, 'employee_profile') and user.employee_profile.is_branch_admin:
            # Branch admins can update employees in their branch
            if instance.branch != user.employee_profile.branch:
                raise PermissionDenied("You can only update employees in your branch")
            
            # Only revoke permissions, not branch admin status
            if 'can_create' in serializer.validated_data:
                instance.can_create = serializer.validated_data['can_create']
            if 'can_edit' in serializer.validated_data:
                instance.can_edit = serializer.validated_data['can_edit']
            if 'can_delete' in serializer.validated_data:
                instance.can_delete = serializer.validated_data['can_delete']
            
            if 'is_branch_admin' in serializer.validated_data:
                instance.is_branch_admin = serializer.validated_data['is_branch_admin']
                
            serializer.save(modified_by=user)

        elif instance.user == user:
            # Employees can update only specific fields about themselves
            allowed_fields = {
                'mobile_number', 'address', 'landmark', 'city',
                'state', 'pincode', 'designation'
            }
            
            # Filter the validated data to only include allowed fields
            filtered_data = {
                k: v for k, v in serializer.validated_data.items()
                if k in allowed_fields
            }
            
            # Update the instance with filtered data
            for field, value in filtered_data.items():
                setattr(instance, field, value)
            instance.save()
        else:
            raise PermissionDenied("You don't have permission to edit this employee")

    def perform_destroy(self, instance):
        user = self.request.user
        
        if user.is_superuser:
            if instance.is_superuser:
                raise PermissionDenied("Cannot delete other superusers")
            instance.delete()
            return
        
        if instance.user == user:
            raise PermissionDenied("You cannot delete yourself")
            
        if hasattr(user, 'employee_profile'):
            employee = user.employee_profile
            
            # Don't allow deleting yourself
            if instance.user == user:
                raise PermissionDenied("You cannot delete yourself")
                
            # Branch admins can delete employees in their branch (except other admins)
            if employee.is_branch_admin and instance.branch == employee.branch:
                if not instance.is_branch_admin:  # Can't delete other branch admins
                    instance.delete()
                    return
                    
            # Employee admins with delete permission can delete regular employees
            if employee.can_delete and instance.branch == employee.branch:
                if not any([
                instance.is_branch_admin,
                instance.is_superuser,
                instance.can_create,
                instance.can_edit,
                instance.can_delete
            ]):  # Can't delete other admins
                    instance.delete()
                    return
                    
        raise PermissionDenied("You don't have permission to delete this employee")
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    