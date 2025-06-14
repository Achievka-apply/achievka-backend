# universities/admin.py
from django.contrib import admin
from .models import (
    University,
    Program,
    Scholarship,
    UniversityFavorite,
    ProgramFavorite,
    ScholarshipFavorite,
)

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'city', 'study_format')
    search_fields = ('name', 'country', 'city')
    list_filter  = ('study_format',)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display    = ('name', 'university', 'study_type', 'study_format', 'tuition_fee', 'deadline')
    search_fields   = ('name', 'university__name', 'city', 'country')
    list_filter     = ('study_type', 'study_format')
    autocomplete_fields = ('university',)


@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display  = ('name', 'country', 'amount', 'deadline', 'result_date')
    search_fields = ('name', 'country')
    list_filter   = ('country',)


@admin.register(UniversityFavorite)
class UniversityFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'university', 'created_at')
    autocomplete_fields = ('user', 'university')


@admin.register(ProgramFavorite)
class ProgramFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'created_at')
    autocomplete_fields = ('user', 'program')


@admin.register(ScholarshipFavorite)
class ScholarshipFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'scholarship', 'created_at')
    autocomplete_fields = ('user', 'scholarship')
from django.contrib import admin

# Register your models here.
