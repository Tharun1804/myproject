from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Organisation, Branch, Company, Employee
from django import forms
from django.contrib import messages

class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    def clean_is_superuser(self):
        if not self.instance.is_superuser and self.cleaned_data['is_superuser']:
            if not self.current_user.is_superuser:
                raise forms.ValidationError("Only superusers can create other superusers")
        return self.cleaned_data['is_superuser']

class CustomUserAdmin(UserAdmin):
    form = UserAdminForm
    list_display = ('email', 'name', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form

    def save_model(self, request, obj, form, change):
        if obj.is_superuser and not request.user.is_superuser:
            messages.error(request, "Only superusers can create other superusers")
            obj.is_superuser = False
        
        if obj.is_staff and not request.user.is_superuser:
            messages.error(request, "Only superusers can make users staff")
            obj.is_staff = False
            
        super().save_model(request, obj, form, change)

admin.site.register(User, CustomUserAdmin)

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'city', 'state', 'is_active')
    search_fields = ('name', 'email')
    list_filter = ('is_active',)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'organisation', 'admin', 'email', 'city', 'state', 'is_active')
    search_fields = ('name', 'email')
    list_filter = ('is_active', 'organisation')
    raw_id_fields = ('admin',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(admin=request.user)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and obj.admin == request.user:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "admin":
            kwargs["queryset"] = User.objects.filter(is_superuser=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'email', 'city', 'state', 'is_active')
    search_fields = ('name', 'email')
    list_filter = ('is_active', 'branch')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(branch__admin=request.user)

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.branch_admin_of.exists()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and obj.branch.admin == request.user:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch', 'designation', 'can_create', 'can_edit', 'can_delete', 'is_active')
    list_filter = ('branch', 'designation', 'can_create', 'can_edit', 'can_delete', 'is_active')
    raw_id_fields = ('user', 'branch', 'company')
    search_fields = ('user__name', 'user__email')
    
    fieldsets = (
        (None, {
            'fields': ('email', 'branch', 'company')
        }),
        ('Personal Information', {
            'fields': ('name','mobile_number', 'address', 'landmark', 'city', 'state', 'pincode')
        }),
        ('Employment Details', {
            'fields': ('designation', 'salary', 'joining_date', 'date_of_birth')
        }),
        ('Permissions', {
            'fields': ('is_branch_admin','is_superuser','can_create', 'can_edit', 'can_delete')
        }),
        ('Status', {
            'fields': ('is_active', 'is_delete')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(branch__admin=request.user)

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.branch_admin_of.exists()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and obj.branch.admin == request.user:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and obj.branch.admin == request.user:
            return True
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "branch":
            if not request.user.is_superuser:
                kwargs["queryset"] = Branch.objects.filter(admin=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        if not obj.user:
            # Automatically create user if none exists
            user = User.objects.create_user(
                email=f"{obj.name.replace(' ', '').lower()}@company.com",
                name=obj.name,
                password=User.objects.make_random_password()
            )
            obj.user = user
        super().save_model(request, obj, form, change)