# users/oauth_clients.py

from allauth.socialaccount.providers.oauth2.client import OAuth2Client


class PatchedOAuth2Client(OAuth2Client):
    def __init__(self, request, callback_url=None, client_id=None, scope=None, **kwargs):
        # игнорируем дублирующийся scope_delimiter
        kwargs.pop("scope_delimiter", None)
        super().__init__(request, callback_url=callback_url, client_id=client_id, scope=scope, **kwargs)
