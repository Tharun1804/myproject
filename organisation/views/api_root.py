from django.shortcuts import render
from django.urls import reverse as django_reverse

def api_root(request):
    has_employee_profile = hasattr(request.user, 'employee_profile')
    is_branch_admin = False
    branch_id = None
    employee_profile_id = None
    can_delete = False
    
    if has_employee_profile:
        is_branch_admin = request.user.employee_profile.is_branch_admin
        if request.user.employee_profile.branch:
            branch_id = request.user.employee_profile.branch.id
        employee_profile_id = request.user.employee_profile.id
        can_delete = request.user.employee_profile.can_delete

    context = {
        'api_urls': {
            'organisations': django_reverse('organisation-list'),
            'branches': django_reverse('branch-list'),
            'companies': django_reverse('company-list'),
            'employees': django_reverse('employee-list'),
        },
        'has_employee_profile': has_employee_profile,
        'is_branch_admin': is_branch_admin,
        'branch_id': branch_id,
        'employee_profile_id': employee_profile_id,
        'can_delete': can_delete
    }
    return render(request, 'api_root.html', context)