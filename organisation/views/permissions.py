from rest_framework.permissions import BasePermission, SAFE_METHODS
from ..models import Employee, Branch

class IsSuperuserOrBranchAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'employee_profile') and request.user.employee_profile.is_branch_admin

class IsSuperuserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_superuser

class IsBranchAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
            
        if not request.user.is_authenticated:
            return False
            
        if hasattr(request.user, 'branch_admin_of'):
            return True
            
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
            
        if not hasattr(request.user, 'branch_admin_of'):
            return False
            
        # Allow branch admin to access their branch's data
        if isinstance(obj, Branch):
            return obj.admin == request.user
            
        # Allow branch admin to access their branch's employees
        if isinstance(obj, Employee):
            return obj.branch.admin == request.user
            
        return False

class IsEmployeeReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

class CanCreateEmployee(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser or (hasattr(request.user, 'employee_profile') and request.user.employee_profile.is_branch_admin):
            return True
        
        if hasattr(request.user, 'employee_profile'):
            employee = request.user.employee_profile
            return employee.is_branch_admin or employee.can_create
            
        return False

class CanEditEmployee(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser or (hasattr(request.user, 'employee_profile') and request.user.employee_profile.is_branch_admin):
            return True
        
        if hasattr(request.user, 'employee_profile'):
            employee = request.user.employee_profile
            # Allow editing own profile
            if str(view.kwargs.get('pk')) == str(employee.id):
                return True
            return employee.is_branch_admin or employee.can_edit
            
        return False

class CanDeleteEmployee(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        
        if request.user.is_superuser or (hasattr(request.user, 'employee_profile') and request.user.employee_profile.is_branch_admin):
            return True
        
        if hasattr(request.user, 'employee_profile'):
            employee = request.user.employee_profile
            return employee.is_branch_admin or employee.can_delete
            
        return False