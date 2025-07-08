from django.urls import path, include
from .views.organisation_views import OrganisationCRUDView
from .views.branch_views import BranchCRUDView
from .views.company_views import CompanyCRUDView
from .views.employee_views import EmployeeCRUDView
from rest_framework_simplejwt.views import TokenRefreshView
from .views.token_views import CustomTokenObtainPairView
from .views.frontend_views import employee_login, employee_logout, employee_home
from .views.api_root import api_root
from .views.check_username import check_username



urlpatterns = [
    # API Root
    path('', api_root, name='api-root'),

    # JWT Authentication
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Organisations
    path('organisations/', OrganisationCRUDView.as_view(), name='organisation-list'),
    path('organisations/<int:pk>/', OrganisationCRUDView.as_view(), name='organisation-detail'),

    # Branches
    path('branches/', BranchCRUDView.as_view(), name='branch-list'),
    path('branches/<int:pk>/', BranchCRUDView.as_view(), name='branch-detail'),
    

    # Companies
    path('companies/', CompanyCRUDView.as_view(), name='company-list'),
    path('companies/<int:pk>/', CompanyCRUDView.as_view(), name='company-detail'),

    # Employees
    path('employees/', EmployeeCRUDView.as_view(), name='employee-list'),
    path('employees/<int:pk>/', EmployeeCRUDView.as_view(), name='employee-detail'),
    

    # Frontend views
    path('login/', employee_login, name='employee_login'),
    path('home/', employee_home, name='employee_home'),
    path('logout/', employee_logout, name='employee_logout'),
    
    path('employees/create/', EmployeeCRUDView.as_view(), name='employee-create'),
    path('users/check_username/', check_username, name='check_username'),
    # path('employees/check_email/', views.check_email_exists, name='check_email'),
]