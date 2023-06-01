from django.contrib.auth.models import User
from account.models import Profile

def create_profile(backend, user, *args, **kwargs):
    Profile.objects.get_or_create(user=user)

class EmailAuthBackend:
    def authenticate(self, request, email=None, password=None):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
            return None
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
