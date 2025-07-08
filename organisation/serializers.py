from rest_framework import serializers
from .models import Organisation, Branch, Company, Employee, User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings
import logging
from datetime import datetime, date


logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'is_active', 'is_staff', 'is_superuser']
        read_only_fields = ['is_active', 'is_staff', 'is_superuser']

class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = '__all__'
        read_only_fields = ('created_at', 'modified_at', 'created_by', 'modified_by', 'is_delete')
        
    def validate(self, data):
        if 'name' not in data or not data['name']:
            raise serializers.ValidationError({"name": "This field is required."})
        return data

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'
        read_only_fields = ('created_at', 'modified_at', 'created_by', 'modified_by', 'is_delete', 'admin')

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ('created_at', 'modified_at', 'created_by', 'modified_by', 'is_delete')

class EmployeeSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    user = UserSerializer(required=False)
    can_create = serializers.BooleanField(required=False)
    can_edit = serializers.BooleanField(required=False)
    can_delete = serializers.BooleanField(required=False)
    is_branch_admin = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(write_only=True, required=True)
    name = serializers.CharField( write_only=True, required=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'email','user','password','mobile_number', 'address', 'landmark','city', 'state',
            'pincode', 'branch', 'company', 'designation', 'salary', 'name','country',
            'joining_date', 'date_of_birth', 'is_branch_admin', 'is_active', 'is_branch_admin', 'is_superuser',
            'can_create', 'can_edit', 'can_delete', 'age'
        ]
        read_only_fields = ('created_at', 'modified_at', 'created_by', 'modified_by', 'age', 'is_branch_admin')

    def get_is_branch_admin(self, obj):
        if not hasattr(obj, 'user') or not obj.user:
            return False
        return obj.is_branch_admin

    def to_representation(self, instance):
        try:
            data = super().to_representation(instance)
            if not hasattr(instance, 'user') or not instance.user:
                data['user'] = None
            return data
        except Exception as e:
            logger.error(f"Error serializing employee: {str(e)}")
            return {'error': 'Employee data could not be loaded'}

    # Update the update method in EmployeeSerializer
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        
        # Update user without any checks
        if hasattr(instance, 'user') and instance.user and user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        
        # Update employee fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
    
    def validate(self, data):
        # Handle cases where city/state might be datetime objects
        if 'city' in data and isinstance(data['city'], (datetime, date)):
            data['city'] = ""
        if 'state' in data and isinstance(data['state'], (datetime, date)):
            data['state'] = ""
        
        # No email validation at all - completely removed
        return data
    
    def create_(self, validated_data):
        # Get password from validated_data (it's at top level from your form)
        password = validated_data.pop('password')
        
        # Get user data - either from nested user object or create it
        user_data = validated_data.pop('user', {})
        
        # If email/name aren't in user_data, check top level (for backward compatibility)
        email = user_data.get('email', validated_data.pop('email', None))
        name = user_data.get('name', validated_data.pop('name', None))
        
        if not email:
            raise serializers.ValidationError({"email": "This field is required."})
        if not name:
            raise serializers.ValidationError({"name": "This field is required."})
        if not password:
            raise serializers.ValidationError({"password": "This field is required."})

        # Create the user
        user = User.objects.create_user(
            email=user_data.get('email'),
            name=user_data.get('name'),
            password=user_data.get('password'),
            is_active=True
        )
        
        # Create the employee
        employee = Employee.objects.create(user=user, **validated_data)
        return employee
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not (self.user.is_superuser or hasattr(self.user, 'employee_profile')):
            raise serializers.ValidationError("User has no employee profile")
        return data