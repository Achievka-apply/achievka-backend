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
    # ======================
    #      Universities
    # ======================

    # Список университетов (with filters, search, ordering)
    path(
        'universities/',
        UniversityViewSet.as_view({'get': 'list'}),
        name='university-list'
    ),
    # Детали конкретного университета
    path(
        'universities/<int:pk>/',
        UniversityViewSet.as_view({'get': 'retrieve'}),
        name='university-detail'
    ),
    # Autocomplete (подсказки при вводе текста для поля name)
    path(
        'universities/autocomplete/',
        UniversityViewSet.as_view({'get': 'autocomplete'}),
        name='university-autocomplete'
    ),


    # ======================
    #       Programs
    # ======================

    # Список программ (with filters, search, ordering)
    path(
        'programs/',
        ProgramViewSet.as_view({'get': 'list'}),
        name='program-list'
    ),
    # Детали конкретной программы
    path(
        'programs/<int:pk>/',
        ProgramViewSet.as_view({'get': 'retrieve'}),
        name='program-detail'
    ),
    # Autocomplete по программам
    path(
        'programs/autocomplete/',
        ProgramViewSet.as_view({'get': 'autocomplete'}),
        name='program-autocomplete'
    ),


    # ======================
    #     Scholarships
    # ======================

    # Список грантов (with filters, search, ordering)
    path(
        'scholarships/',
        ScholarshipViewSet.as_view({'get': 'list'}),
        name='scholarship-list'
    ),
    # Детали конкретного гранта
    path(
        'scholarships/<int:pk>/',
        ScholarshipViewSet.as_view({'get': 'retrieve'}),
        name='scholarship-detail'
    ),
    # Autocomplete по грантам
    path(
        'scholarships/autocomplete/',
        ScholarshipViewSet.as_view({'get': 'autocomplete'}),
        name='scholarship-autocomplete'
    ),


    # ======================
    #  Favorites: Universities
    # ======================

    # Список избранных университетов / добавить новый favorite
    path(
        'favorites/universities/',
        UniversityFavoriteViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='fav-university-list'
    ),
    # Детальная работа с favorite: retrieve, partial_update (PATCH), delete
    path(
        'favorites/universities/<int:pk>/',
        UniversityFavoriteViewSet.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='fav-university-detail'
    ),
    # Переупорядочивание всех университетов в избранном
    path(
        'favorites/universities/reorder/',
        UniversityFavoriteViewSet.as_view({'post': 'reorder'}),
        name='fav-university-reorder'
    ),


    # ======================
    #   Favorites: Programs
    # ======================

    # Список избранных программ / добавить новую
    path(
        'favorites/programs/',
        ProgramFavoriteViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='fav-program-list'
    ),
    # Детальная работа с favorite: retrieve, partial_update (PATCH), delete
    path(
        'favorites/programs/<int:pk>/',
        ProgramFavoriteViewSet.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='fav-program-detail'
    ),
    # Переупорядочивание всех программ в избранном
    path(
        'favorites/programs/reorder/',
        ProgramFavoriteViewSet.as_view({'post': 'reorder'}),
        name='fav-program-reorder'
    ),


    # ======================
    #  Favorites: Scholarships
    # ======================

    # Список избранных грантов / добавить новый
    path(
        'favorites/scholarships/',
        ScholarshipFavoriteViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='fav-scholarship-list'
    ),
    # Детальная работа с favorite: retrieve, partial_update (PATCH), delete
    path(
        'favorites/scholarships/<int:pk>/',
        ScholarshipFavoriteViewSet.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='fav-scholarship-detail'
    ),
    # Переупорядочивание всех грантов в избранном
    path(
        'favorites/scholarships/reorder/',
        ScholarshipFavoriteViewSet.as_view({'post': 'reorder'}),
        name='fav-scholarship-reorder'
    ),
]
