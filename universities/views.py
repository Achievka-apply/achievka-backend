#universities/views.py
from rest_framework import viewsets, mixins, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import (
    University, Program, Scholarship,
    UniversityFavorite, ProgramFavorite, ScholarshipFavorite
)
from .serializers import (
    UniversityMiniSerializer, UniversityDetailSerializer,
    ProgramMiniSerializer, ProgramDetailSerializer,
    ScholarshipMiniSerializer, ScholarshipDetailSerializer,
    UniversityFavoriteSerializer, ProgramFavoriteSerializer, ScholarshipFavoriteSerializer
)
from .filters import UniversityFilter, ProgramFilter, ScholarshipFilter

# Права доступа: только владелец может удалять свой favorite
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


# — Основные ViewSet’ы —

class UniversityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = University.objects.all()
    filter_backends  = [DjangoFilterBackend, SearchFilter]
    filterset_class  = UniversityFilter
    search_fields    = ["name","city","country"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UniversityDetailSerializer
        return UniversityMiniSerializer


class ProgramViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = Program.objects.select_related("university")
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class  = ProgramFilter
    search_fields    = ["name","university__name","city","country"]
    ordering_fields  = ["tuition_fee","deadline"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProgramDetailSerializer
        return ProgramMiniSerializer


class ScholarshipViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = Scholarship.objects.all()
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class  = ScholarshipFilter
    search_fields    = ["name","country"]
    ordering_fields  = ["amount","deadline"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ScholarshipDetailSerializer
        return ScholarshipMiniSerializer


# — ViewSet’ы избранного —

class UniversityFavoriteViewSet(
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        mixins.DestroyModelMixin,
        viewsets.GenericViewSet):
    serializer_class   = UniversityFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return UniversityFavorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProgramFavoriteViewSet(
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        mixins.DestroyModelMixin,
        viewsets.GenericViewSet):
    serializer_class   = ProgramFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return ProgramFavorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ScholarshipFavoriteViewSet(
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        mixins.DestroyModelMixin,
        viewsets.GenericViewSet):
    serializer_class   = ScholarshipFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return ScholarshipFavorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
