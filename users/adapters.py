# users/adapters.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.contrib.auth import get_user_model

User = get_user_model()

class AutoConnectSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin: SocialLogin):
        """
        Если почта от провайдера уже есть у нас в системе,
        просто «подцепляем» этот sociallogin к существующему пользователю.
        """
        # Если аккаунт уже привязан — ничего не делаем
        if sociallogin.is_existing:
            return

        email = getattr(sociallogin.user, "email", None)
        if not email:
            return

        try:
            existing = User.objects.get(email__iexact=email)
            sociallogin.connect(request, existing)
        except User.DoesNotExist:
            # Первый раз — идём по региструальному пути
            pass
