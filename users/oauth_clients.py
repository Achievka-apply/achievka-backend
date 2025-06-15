# users/oauth_clients.py

from allauth.socialaccount.providers.oauth2.client import OAuth2Client

class PatchedOAuth2Client(OAuth2Client):
    def __init__(self, *args, **kwargs):
        # Убираем дублирующийся аргумент, если он есть
        kwargs.pop("scope_delimiter", None)
        super().__init__(*args, **kwargs)
