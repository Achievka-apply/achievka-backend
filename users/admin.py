# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm

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
