
from django.urls import path
from .views import LetterViewSet

app_name = 'letters'

urlpatterns = [
    path(
        'letters/',
        LetterViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='letter-list'
    ),
    path(
        'letters/<uuid:pk>/',
        LetterViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='letter-detail'
    ),
    path(
        'letters/<uuid:pk>/versions/',
        LetterViewSet.as_view({'get': 'versions', 'post': 'versions'}),
        name='letter-versions'
    ),
    path(
        'letters/<uuid:pk>/analyse_stream/',
        LetterViewSet.as_view({'post': 'analyse_stream'}),
        name='letter-analyse-stream'
    ),
]