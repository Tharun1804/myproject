class JWTSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only set auth header if user is authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            if 'access_token' in request.session:
                auth_header = f"Bearer {request.session['access_token']}"
                request.META['HTTP_AUTHORIZATION'] = auth_header
            
            access_token = request.COOKIES.get('access_token')
            if access_token:
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
                
        return self.get_response(request)