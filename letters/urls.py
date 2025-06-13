# letters/urls.py
from django.urls import path
from .views import LetterViewSet

app_name = 'letters'

urlpatterns = [
    # список и создание писем
    path(
        'letters/',
        LetterViewSet.as_view({
            'get':  'list',
            'post': 'create',
        }),
        name='letter-list'
    ),

    # деталка, обновление, удаление конкретного письма
    path(
        'letters/<uuid:pk>/',
        LetterViewSet.as_view({
            'get':    'retrieve',
            'put':    'update',
            'patch':  'partial_update',
            'delete': 'destroy',
        }),
        name='letter-detail'
    ),

    # версии письма: список и создание новой (autosave или ручной «проверить снова»)
    path(
        'letters/<uuid:pk>/versions/',
        LetterViewSet.as_view({
            'get':  'versions',
            'post': 'versions',
        }),
        name='letter-versions'
    ),
]
