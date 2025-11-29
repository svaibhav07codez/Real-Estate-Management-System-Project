"""
Custom Middleware - NO ORM
Adds user to request from session data
"""

from .auth_utils import SimpleUser


class CustomUserMiddleware:
    """
    Adds SimpleUser object to request.user
    Uses ONLY session data - NO database queries, NO ORM
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add user object to request based on session
        if request.session.get('is_authenticated'):
            request.user = SimpleUser(request.session)
        else:
            # Anonymous user
            request.user = SimpleUser({'is_authenticated': False})
        
        response = self.get_response(request)
        return response
