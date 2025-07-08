from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

def employee_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')  # Make sure form uses 'email' not 'username'
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        
        if  user is not None and user is not None:
            if user.is_active:  # Check if user is active
                login(request, user)
                refresh = RefreshToken.for_user(user)
                
                response = HttpResponseRedirect(reverse('employee_home'))
                response.set_cookie(
                    'access_token', 
                    str(refresh.access_token),
                    httponly=True,
                    secure=settings.SESSION_COOKIE_SECURE,
                    samesite='Lax'
                )
                request.session['access_token'] = str(refresh.access_token)
                return response
            else:
                return render(request, 'employee_login.html', {
                    'error': 'Account is not active'
                })
        else:
            return render(request, 'employee_login.html', {
                'error': 'Invalid email or password'
            })
    
    return render(request, 'employee_login.html')

@login_required
def employee_logout(request):
    logger.debug(f"Logging out user: {request.user.email}")  # Changed from username to email
    # Clear session and cookies
    if 'access_token' in request.session:
        del request.session['access_token']
    
    response = redirect(reverse('employee_login'))
    response.delete_cookie('access_token')
    logout(request)
    return response

@login_required
def employee_home(request):
    try:
        # Handle superusers who don't have employee profile
        if request.user.is_superuser:
            from django.contrib.auth.models import User
            from ..models import Branch, Organisation, Company
            # Create dummy context for superuser
            context = {
                'employee': {
                    'name': 'request.user.name',
                    'email': request.user.email,
                    'mobile_number': '',
                    'designation': 'System Administrator',
                    'joining_date': '',
                    'salary': '',
                    'age': ''
                },
                'branch': Branch.objects.first(),
                'organisation': Organisation.objects.first(),
                'company': Company.objects.first(),
                'is_branch_admin': request.user.employee_profile.is_branch_admin if hasattr(request.user, 'employee_profile') else False,
                'is_regular_employee': not (request.user.is_superuser or 
                                    (hasattr(request.user, 'employee_profile') and 
                                     request.user.employee_profile.is_branch_admin)),
                'is_superuser': request.user.is_superuser,
            }
            return render(request, 'employee_home.html', context)
        else:
            employee = request.user.employee_profile
            branch = employee.branch
            organisation = branch.organisation if branch else None
            
            # Safely get company information
            company = None
            if branch and hasattr(branch, 'company'):
                company = branch.company
            elif branch and hasattr(branch, 'companies'):  # If it's a many-to-many relationship
                company = branch.companies.first()
            
            context = {
                'employee': employee,
                'branch': branch,
                'organisation': organisation,
                'company': company,
                'is_superuser': request.user.is_superuser,
                'is_branch_admin': employee.is_branch_admin if hasattr(employee, 'is_branch_admin') else False
            }
        request.user.refresh_from_db()
        return render(request, 'employee_home.html', context)
    
    except Exception as e:
        logger.error(f"Error in employee_home: {str(e)}")
        logout(request)
        return redirect(reverse('employee_login'))