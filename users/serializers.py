from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import PasswordResetForm
from .models import Profile,OnboardingResponse

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model  = User
        fields = ('email', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(
            #username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password']
        )

class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid            = serializers.CharField()
    token          = serializers.CharField()
    new_password1  = serializers.CharField(write_only=True)
    new_password2  = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password1'] != attrs['new_password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        return attrs

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        source='user.email', read_only=True
    )
    has_subscription = serializers.BooleanField(
        source='user.has_subscription',
        read_only=True
    )
    class Meta:
        model  = Profile
        fields = (
            'email',
            'first_name',
            'last_name',
            'bio',
            'avatar',
            'updated_at',
            'has_subscription',

        )
        read_only_fields = ('updated_at',)

# onboarding/serializers.py


class OnboardingResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OnboardingResponse
        fields = [
            'question_index',
            'answer_text',
            'answer_choices',
        ]
