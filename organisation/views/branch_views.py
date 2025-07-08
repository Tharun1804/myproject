from rest_framework.response import Response
from django.core.exceptions import PermissionDenied
from organisation.models import Branch
from organisation.serializers import BranchSerializer
from .base_view import BaseCRUDView
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from .permissions import IsBranchAdmin

class BranchCRUDView(BaseCRUDView):
    serializer_class = BranchSerializer
    queryset = Branch.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return super().get_queryset()
        if hasattr(user, 'employee_profile'):
            employee = user.employee_profile
            if employee.branch:
            # Return only the employee's branch
                return queryset.filter(id=employee.branch.id)
        return queryset.none()

    def perform_create(self, serializer):
        # Only superusers should be able to create branches
        if not self.request.user.is_superuser:
            raise PermissionDenied("Only superusers can create branches")
        serializer.save(created_by=self.request.user, modified_by=self.request.user)

        if self.request.user.is_superuser:
            serializer.save(created_by=self.request.user, modified_by=self.request.user) 
            return
        elif hasattr(self.request.user, 'employee_profile') and self.request.user.employee_profile.is_branch_admin:
            serializer.save(created_by=self.request.user, modified_by=self.request.user)
        else:
            raise PermissionDenied("Only branch admins or superusers can create branches")

    def perform_update(self, serializer):
        # Branch admins can only update their own branch
        if self.request.user.is_superuser:
            serializer.save(modified_by=self.request.user)
        elif hasattr(self.request.user, 'employee_profile') and self.request.user.employee_profile.is_branch_admin:
            if serializer.instance != self.request.user.employee_profile.branch:
                raise PermissionDenied("You can only update your own branch")
            serializer.save(modified_by=self.request.user)
        else:
            raise PermissionDenied("You don't have permission to update branches")

    def perform_destroy(self, instance):
        if self.request.user.is_superuser:
            return super().perform_destroy(instance)
        elif hasattr(self.request.user, 'employee_profile') and self.request.user.employee_profile.is_branch_admin:
            if instance != self.request.user.employee_profile.branch:
                raise PermissionDenied("Branch admins can only delete their own branch")
            return super().perform_destroy(instance)
        else:
            raise PermissionDenied("Only superusers or branch admins can delete branches")

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsBranchAdmin()]
    

    def revoke_branch_admin(self, request, pk=None):
        """Revoke branch admin status from an employee"""
        branch = self.get_object()
        employee_id = request.data.get('employee_id')
        
        if not employee_id:
            return Response({"error": "Employee ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            employee = Employee.objects.get(id=employee_id, branch=branch)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found in this branch"}, status=status.HTTP_404_NOT_FOUND)
        
        # Only superusers can revoke branch admin status
        if not request.user.is_superuser:
            return Response({"error": "Only superusers can revoke branch admin status"}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        # Revoke admin status
        employee.revoke_branch_admin()
        return Response({"message": "Branch admin status revoked successfully"})