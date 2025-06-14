from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email      = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name  = models.CharField(max_length=30, blank=True)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    has_subscription = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


class Profile(models.Model):
    user       = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    first_name = models.CharField(max_length=30, blank=True)
    last_name  = models.CharField(max_length=30, blank=True)
    bio        = models.TextField(blank=True)
    avatar     = models.ImageField(
        upload_to='avatars/', blank=True, null=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile of {self.user.email}'


class OnboardingResponse(models.Model):
    user           = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='onboarding_responses'
    )
    # просто порядковый номер или ключ вопроса, который знает фронт
    question_index = models.IntegerField()
    # для текстовых вопросов
    answer_text    = models.TextField(blank=True, null=True)
    # для single/multi — массив выбранных вариантов
    answer_choices = ArrayField(
        base_field=models.CharField(max_length=200),
        blank=True,
        default=list
    )
    answered_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'question_index')
        ordering        = ['question_index']

    def __str__(self):
        return f"User {self.user_id} → Q{self.question_index}"

class Newsletter(models.Model):
    subject = models.CharField('Тема', max_length=200)
    body    = models.TextField('Текст письма')
    created = models.DateTimeField(auto_now_add=True)
    sent    = models.BooleanField('Отправлено', default=False)

    def __str__(self):
        return f'{self.subject} — {"✓" if self.sent else "…"}'