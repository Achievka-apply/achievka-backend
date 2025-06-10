# users/admin.py
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User,Newsletter
from .forms import CustomUserCreationForm, CustomUserChangeForm
import threading

from django.contrib import admin, messages
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth import get_user_model


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form     = CustomUserChangeForm
    model    = User

    list_display  = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter   = ('is_staff', 'is_active')
    ordering      = ('email',)

    fieldsets = (
        (None,             {'fields': ('email', 'password')}),
        ('Personal info',  {'fields': ('first_name', 'last_name')}),
        ('Permissions',    {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display    = ('subject', 'created', 'sent')
    readonly_fields = ('created', 'sent')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not obj.sent:
            # собираем список email-ов всех активных пользователей
            User = get_user_model()
            emails = list(
                User.objects
                    .filter(is_active=True)
                    .values_list('email', flat=True)
                    .exclude(email__exact='')
            )

            # формируем одно письмо с BCC-списком
            msg = EmailMessage(
                subject=obj.subject,
                body=obj.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[],           # пустой TO
                bcc=emails,      # все в BCC
            )

            # отправляем в фоне, чтобы не блокировать админку
            threading.Thread(
                target=msg.send,
                kwargs={'fail_silently': False},
                daemon=True
            ).start()

            # помечаем как отправленное
            obj.sent = True
            obj.save(update_fields=['sent'])

            self.message_user(
                request,
                f'📨 Фоновая рассылка запущена ({len(emails)} адресов).',
                level=messages.SUCCESS
            )
