# users/views.py

from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from .serializers import ProfileSerializer
from .models import Profile, OnboardingResponse
from django.core.mail import send_mail
from drf_yasg.utils import swagger_auto_schema
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.microsoft.views import MicrosoftGraphOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from rest_framework_simplejwt.views import TokenRefreshView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from users.oauth_clients import PatchedOAuth2Client

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    OnboardingResponseSerializer
)


from .models import User

User = get_user_model()

class CustomRegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"email": user.email},
            status=status.HTTP_201_CREATED
        )


class CustomLoginView(APIView):
    """
    POST /api/auth/login/
    - Валидирует email+password
    - В ответ возвращает JSON { access: "..."}
    - Кладёт refresh-токен в HttpOnly cookie
    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        # используем username=email, если вы настроили USERNAME_FIELD = 'email'
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response(
                {"detail": "Неверные учетные данные"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        refresh_str = str(refresh)

        response = Response({"access": access}, status=status.HTTP_200_OK)
        # Сохраняем refresh в HttpOnly cookie
        response.set_cookie(
            key    = 'refresh_token',
            value  = refresh_str,
            httponly = True,
            secure   = not settings.DEBUG,  # True на проде
            samesite = 'Strict',
           # path     = '/api/auth/token/refresh/'  # доступно только этому пути
        )
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """
    POST /api/auth/token/refresh/
    - Берёт refresh из HttpOnly cookie
    - Валидирует его, отдаёт новый access в теле
    - При ROTATE_REFRESH_TOKENS= True кладёт обновлённый refresh обратно в cookie
    """
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response(
                {"detail": "Refresh token не найден в cookie"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Внедряем токен в стандартный сериализатор
        serializer = self.get_serializer(data={'refresh': refresh_token})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        access     = data['access']
        new_refresh = data.get('refresh', refresh_token)

        # Формируем ответ
        response = Response({"access": access}, status=status.HTTP_200_OK)
        # Обновляем cookie, если ротация включена
        response.set_cookie(
            key     = 'refresh_token',
            value   = str(new_refresh),
            httponly= True,
            secure  = not settings.DEBUG,
            samesite= 'Strict',
            path    = '/api/auth/token/refresh/'
        )
        return response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


class CustomLogoutView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {"detail": "Refresh token not found in cookies."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Invalid refresh token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = Response(status=status.HTTP_204_NO_CONTENT)
        # Optional: delete cookies if needed
        response.delete_cookie('refresh_token')

        return response

class CustomPasswordResetView(APIView):
    """
    Принимает email, проверяет пользователя, генерирует uid+token
    и шлёт письмо на почту с ссылкой на фронтенд.
    """
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"email": "Пользователь с таким email не найден."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 1) генерируем uid и token
        uid   = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # 2) собираем ссылку на фронт
        reset_link = (
            "https://achievka.com/reset-password"
            f"?uid={uid}&token={token}"
        )

        # 3) отправляем письмо
        subject = "Сброс пароля на Achievka"
        message = (
            f"Здравствуйте!\n\n"
            f"Чтобы сбросить пароль, перейдите по ссылке:\n\n"
            f"{reset_link}\n\n"
            f"Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо."
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )

        # 4) подтверждаем отправку письма
        return Response(
            {"detail": "Письмо с инструкциями по сбросу пароля отправлено."},
            status=status.HTTP_200_OK
        )

class CustomPasswordResetConfirmView(APIView):
    """
    Принимает uid, token и новый пароль, проверяет токен и меняет пароль.
    """
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid   = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        pwd   = serializer.validated_data['new_password1']

        try:
            pk = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=pk)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Неверный UID."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Неверный или просроченный токен."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(pwd)
        user.save()

        return Response(
            {"detail": "Пароль успешно сброшен."},
            status=status.HTTP_200_OK
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/profile/       — получить свой профиль
    PATCH/PUT  /api/auth/profile/ — обновить поля профиля
    """
    serializer_class   = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Возвращаем профиль текущего аутентифицированного пользователя
        return self.request.user.profile







class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class  = PatchedOAuth2Client

    # ← этот атрибут нужен обязательно, чтобы не было ошибки "Define callback_url in view"
    callback_url = "https://dev.achievka.com/google/callback/"

    def get_callback_url(self, request):
        # если фронтенд прислал в POST поле redirect_uri — используем его,
        # иначе упадём на статический атрибут выше
        return request.data.get('redirect_uri') or self.callback_url

# Facebook
class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter
    client_class  = PatchedOAuth2Client
    callback_url  = "https://dev.achievka.com/facebook/callback"
    def get_callback_url(self, request):
        # если фронтенд прислал в POST поле redirect_uri — используем его,
        # иначе упадём на статический атрибут выше
        return request.data.get('redirect_uri') or self.callback_url
# Microsoft
class MicrosoftLogin(SocialLoginView):
    adapter_class = MicrosoftGraphOAuth2Adapter
    client_class  = PatchedOAuth2Client
    callback_url   = "https://dev.achievka.com/microsoft/callback/"
    def get_callback_url(self, request):
        # если фронтенд прислал в POST поле redirect_uri — используем его,
        # иначе упадём на статический атрибут выше
        return request.data.get('redirect_uri') or self.callback_url
# Apple
class AppleLogin(SocialLoginView):
    adapter_class = AppleOAuth2Adapter


# onboarding/views.py



class OnboardingResponseCreateView(APIView):
    """
    POST /api/auth/responses/
    Принимает JSON:
    {
      "responses": [
        { "question_index": 0, "answer_text": "Иван Иванов",                "answer_choices": [] },
        { "question_index": 1, "answer_text": null,                         "answer_choices": ["Instagram"] },
        { "question_index": 5, "answer_text": null,                         "answer_choices": ["A","B"] },
        …
      ]
    }
    Сохраняет или обновляет ответы для текущего пользователя.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payload = request.data.get('responses')
        if not isinstance(payload, list):
            return Response(
                {'detail': 'Нужен список responses'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        saved = []
        for item in payload:
            ser = OnboardingResponseSerializer(data=item)
            ser.is_valid(raise_exception=True)

            qidx   = ser.validated_data['question_index']
            text   = ser.validated_data.get('answer_text', None)
            choices= ser.validated_data.get('answer_choices', [])

            obj, created = OnboardingResponse.objects.update_or_create(
                user=user,
                question_index=qidx,
                defaults={
                    'answer_text':    text,
                    'answer_choices': choices
                }
            )
            saved.append({'question_index': qidx, 'id': obj.pk})

        return Response(
            {'detail': 'Ответы сохранены', 'saved': saved},
            status=status.HTTP_200_OK
        )
