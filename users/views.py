from rest_framework import status
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

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer
)
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
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            email=serializer.validated_data['email'],
            username=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        if not user:
            return Response(
                {"detail": "Неверные учетные данные"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            "access" : str(refresh.access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_200_OK)

class CustomLogoutView(APIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Недействительный токен"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

class CustomPasswordResetView(APIView):
    """
    Принимает email, проверяет пользователя и возвращает uid + token
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

        uid   = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        return Response(
            {"uid": uid, "token": token},
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