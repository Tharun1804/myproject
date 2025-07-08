from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import datetime, date
from datetime import date
from django.db.models.signals import post_save
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


from django.dispatch import receiver

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        
        user = self.model(
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return self.email

class BaseModel(models.Model):
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_modified'
    )

    class Meta:
        abstract = True

class Organisation(BaseModel):
    name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=20)
    email = models.EmailField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='India')
    superuser = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organisation_superuser'
    )

    class Meta:
        permissions = [
            ('can_create_organisation', 'Can create organisation'),
        ]

    def __str__(self):
        return self.name

class Branch(BaseModel):
    name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=20)
    email = models.EmailField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='India')
    organisation = models.ForeignKey(
        Organisation, 
        on_delete=models.CASCADE, 
        related_name='branches'
    )
    admin = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='branch_admin_of'
    )

    def __str__(self):
        return f"{self.name} ({self.organisation.name})"

    def save(self, *args, **kwargs):
        # Ensure only one admin per branch
        if self.admin:
            # Remove this branch from any previous admin
            Branch.objects.filter(admin=self.admin).exclude(pk=self.pk).update(admin=None)
        super().save(*args, **kwargs)

class Company(BaseModel):
    name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=20)
    email = models.EmailField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='India')
    branch = models.OneToOneField(
        Branch, 
        on_delete=models.CASCADE, 
        related_name='company'
    )

    def __str__(self):
        return self.name

class Employee(BaseModel):
    name = models.CharField(max_length=255)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        blank=False,
        null=False
    )
    mobile_number = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, validators=[RegexValidator(r'^[A-Za-z ]+$')],blank=True,default="")
    state = models.CharField(max_length=100, validators=[RegexValidator(r'^[A-Za-z ]+$')],blank=True,default="")
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=20, blank=True, null=True)
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE, 
        related_name='employees',
        null=True,
        blank=True
    )
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='employees',
        null=True,
        blank=True
    )
    designation = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    joining_date = models.DateField()
    date_of_birth = models.DateField()
    is_branch_admin = models.BooleanField(default=False, verbose_name="Is Branch Admin")
    is_superuser = models.BooleanField(default=False, verbose_name="Is Superuser")
    can_create = models.BooleanField(default=False, verbose_name="Can Create Records")
    can_edit = models.BooleanField(default=False, verbose_name="Can Edit Records")
    can_delete = models.BooleanField(default=False, verbose_name="Can Delete Records")

    def __str__(self):
        branch_name = self.branch.name if self.branch else "No Branch"
        return f"{self.user.name} ({branch_name})"

    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def is_branch_admin_property(self):
        if not hasattr(self, 'user') or not self.user:
            return False
        return self.branch and self.branch.admin == self.user

    def save(self, *args, **kwargs):
        # Automatically set is_branch_admin if user is branch admin
        if self.branch and self.branch.admin == self.user:
            self.is_branch_admin = True
        
        # Superusers automatically get all permissions
        if self.is_superuser:
            self.is_branch_admin = True
            self.can_create = True
            self.can_edit = True
            self.can_delete = True
        
        super().save(*args, **kwargs)

    
            
    def clean(self):
        super().clean()
        # Ensure city and state are strings
        if isinstance(self.city, (datetime.datetime, datetime.date)):
            self.city = ""
        if isinstance(self.state, (datetime.datetime, datetime.date)):
            self.state = ""


    def revoke_permissions(self):
        """Revoke all permissions from this employee"""
        self.can_create = False
        self.can_edit = False
        self.can_delete = False
        self.save()

    def revoke_branch_admin(self):
        """Revoke branch admin status from this employee"""
        if self.is_branch_admin:
            self.is_branch_admin = False
            # Also revoke permissions when revoking admin status
            self.revoke_permissions()
            self.save()
        
        
        