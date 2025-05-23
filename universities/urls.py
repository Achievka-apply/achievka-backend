# universities/urls.py
from django.urls import path
from .views import (
    UniversityViewSet,
    ProgramViewSet,
    ScholarshipViewSet,
    UniversityFavoriteViewSet,
    ProgramFavoriteViewSet,
    ScholarshipFavoriteViewSet,
)

app_name = 'universities'

urlpatterns = [
    # --- Universities ---
    path(
        'universities/',
        UniversityViewSet.as_view({'get': 'list'}),
        name='university-list'
    ),
    path(
        'universities/<int:pk>/',
        UniversityViewSet.as_view({'get': 'retrieve'}),
        name='university-detail'
    ),

    # --- Programs ---
    path(
        'programs/',
        ProgramViewSet.as_view({'get': 'list'}),
        name='program-list'
    ),
    path(
        'programs/<int:pk>/',
        ProgramViewSet.as_view({'get': 'retrieve'}),
        name='program-detail'
    ),

    # --- Scholarships ---
    path(
        'scholarships/',
        ScholarshipViewSet.as_view({'get': 'list'}),
        name='scholarship-list'
    ),
    path(
        'scholarships/<int:pk>/',
        ScholarshipViewSet.as_view({'get': 'retrieve'}),
        name='scholarship-detail'
    ),

    # --- Favorites: Universities ---
    path(
        'favorites/universities/',
        UniversityFavoriteViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='fav-university-list'
    ),
    path(
        'favorites/universities/<int:pk>/',
        UniversityFavoriteViewSet.as_view({'delete': 'destroy'}),
        name='fav-university-detail'
    ),

    # --- Favorites: Programs ---
    path(
        'favorites/programs/',
        ProgramFavoriteViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='fav-program-list'
    ),
    path(
        'favorites/programs/<int:pk>/',
        ProgramFavoriteViewSet.as_view({'delete': 'destroy'}),
        name='fav-program-detail'
    ),

    # --- Favorites: Scholarships ---
    path(
        'favorites/scholarships/',
        ScholarshipFavoriteViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='fav-scholarship-list'
    ),
    path(
        'favorites/scholarships/<int:pk>/',
        ScholarshipFavoriteViewSet.as_view({'delete': 'destroy'}),
        name='fav-scholarship-detail'
    ),
]
