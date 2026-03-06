from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Allow both 'username' and 'email' as the identifier
        email = kwargs.get('email') or username
        
        if not email or not password:
            return None
            
        try:
            # Check for user by email (case-insensitive)
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Run the default password hasher to prevent timing attacks
            User().set_password(password)
            return None
        except Exception:
            return None
            
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
            
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
