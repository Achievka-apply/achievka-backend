from django.contrib import admin
from .models import Letter, LetterVersion

@admin.register(Letter)
class LetterAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'user', 'updated_at')
    list_filter = ('type',)

@admin.register(LetterVersion)
class LetterVersionAdmin(admin.ModelAdmin):
    list_display = ('letter', 'version_num', 'created_at', 'checked_at')
    list_filter = ('letter__type',)
