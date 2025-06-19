# config/urls.py

from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from letters.views import DraftLetterViewSet

# API definition
schema_view = get_schema_view(
    openapi.Info(
        title="Achievka API",
        default_version='v1',
        description="Документация для achievka-backend",
        terms_of_service="https://achievka.com/terms/",
        contact=openapi.Contact(email="support@achievka.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
router = DefaultRouter()
router.register(r'draft_letters', DraftLetterViewSet, basename='draft_letter')

urlpatterns = [
    path('api/admin/', admin.site.urls),
    path('accounts/', include('allauth.socialaccount.urls')),  # ← здесь

    # ваши приложения
    path('api/auth/', include('users.urls', namespace='users')),
    path('api/',      include('universities.urls', namespace='universities')),
    path('api/', include('letters.urls', namespace='letters')),

    # схемы Swagger / Redoc
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json'),
    re_path(r'^swagger/$',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'),
    re_path(r'^redoc/$',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'),
]

# Раздача медиа в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)