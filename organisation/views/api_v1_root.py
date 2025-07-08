
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

@api_view(['GET'])
def api_v1_root(request, format=None):
    return Response({
        'organisations': reverse('organisation-list', request=request, format=format),
        'branches': reverse('branch-list', request=request, format=format),
        'companies': reverse('company-list', request=request, format=format),
        'employees': reverse('employee-list', request=request, format=format),
        'token-obtain': reverse('token_obtain_pair', request=request, format=format),
        'token-refresh': reverse('token_refresh', request=request, format=format),
    })