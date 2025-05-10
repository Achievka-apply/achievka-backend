from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.conf import settings

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetSerializer
)

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
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        form = PasswordResetForm(data=serializer.validated_data)
        if not form.is_valid():
            return Response(
                {"email": "Пользователь с таким email не найден"},
                status=status.HTTP_400_BAD_REQUEST
            )

        form.save(
            request=request,
            use_https=request.is_secure(),
            email_template_name='users/password_reset_email.html',
            from_email=settings.DEFAULT_FROM_EMAIL,
        )
        return Response(
            {"detail": "Письмо для сброса пароля отправлено"},
            status=status.HTTP_200_OK
        )
