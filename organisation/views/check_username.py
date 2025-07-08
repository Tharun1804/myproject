# check_username.py
from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()

def check_username(request):
    username = request.GET.get('username')
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({'available': not exists})