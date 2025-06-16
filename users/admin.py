# users/admin.py

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.conf import settings
import threading

from .models import User, Newsletter
from .forms import CustomUserCreationForm, CustomUserChangeForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form     = CustomUserChangeForm
    model    = User

    # Добавили has_subscription в columns и фильтрацию
    list_display  = ('email', 'first_name', 'last_name', 'has_subscription', 'is_staff', 'is_active')
    list_filter   = ('has_subscription', 'is_staff', 'is_active')
    ordering      = ('email',)

    # Разбиваем fieldsets и включаем в нужный раздел has_subscription
    fieldsets = (
        (None,             {'fields': ('email', 'password')}),
        ('Personal info',  {'fields': ('first_name', 'last_name')}),
        ('Subscription',   {'fields': ('has_subscription',)}),
        ('Permissions',    {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    # И в add_form тоже показываем флаг подписки
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name',
                'password1', 'password2',
                'has_subscription',  # ← здесь
                'is_staff', 'is_active'
            ),
        }),
    )


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display    = ('subject', 'created', 'sent')
    readonly_fields = ('created', 'sent')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not obj.sent:
            User = get_user_model()
            emails = list(
                User.objects
                    .filter(is_active=True)
                    .values_list('email', flat=True)
                    .exclude(email__exact='')
            )

            msg = EmailMessage(
                subject=obj.subject,
                body=obj.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[],
                bcc=emails,
            )

            threading.Thread(
                target=msg.send,
                kwargs={'fail_silently': False},
                daemon=True
            ).start()

            obj.sent = True
            obj.save(update_fields=['sent'])
            self.message_user(
                request,
                f'📨 Фоновая рассылка запущена ({len(emails)} адресов).',
                level=messages.SUCCESS
            )
