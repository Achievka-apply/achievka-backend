# universities/views.py

from django.db.models import Count, Min
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    University, Program, Scholarship,
    UniversityFavorite, ProgramFavorite, ScholarshipFavorite
)
from .serializers import (
    UniversityMiniSerializer,
    UniversityDetailSerializer,
    ProgramMiniSerializer,
    ProgramDetailSerializer,
    ScholarshipMiniSerializer,
    ScholarshipDetailSerializer,
    UniversityFavoriteSerializer,
    ProgramFavoriteSerializer,
    ScholarshipFavoriteSerializer
)
from .filters import UniversityFilter, ProgramFilter, ScholarshipFilter

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
# ============================
class UniversityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = University.objects.annotate(
        count_programs  = Count("programs", distinct=True),
        min_program_fee = Min("programs__tuition_fee"),
    ).all()

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = UniversityFilter
    search_fields   = ["name", "city", "country"]
    ordering_fields = [
        "name",
        "min_program_fee",
        "count_programs",
    ]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UniversityDetailSerializer
        return UniversityMiniSerializer

    @action(detail=False, methods=["get"])
    def autocomplete(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"results": []})
        matches = University.objects.filter(name__icontains=q)[:10]
        data = [{"id": uni.id, "name": uni.name} for uni in matches]
        return Response({"results": data}, status=status.HTTP_200_OK)


# ============================
#      ProgramViewSet
# ============================

class ProgramViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:     GET /programs/          → список программ (с фильтрами, поиском, сортировкой)
    retrieve: GET /programs/{pk}/    → детальная информация по программе

    autocomplete: GET /programs/autocomplete/?q=<строка>
    """
    queryset = Program.objects.select_related("university").all()

    # Возвращаем ваш FilterSet
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProgramFilter
    search_fields   = ["name", "university__name", "city", "country"]
    ordering_fields = ["tuition_fee", "name", "deadline"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProgramDetailSerializer
        return ProgramMiniSerializer

    @action(detail=False, methods=["get"])
    def autocomplete(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"results": []})
        matches = Program.objects.filter(name__icontains=q)[:10]
        data = [
            {"id": prog.id, "name": prog.name, "university": prog.university.name}
            for prog in matches
        ]
        return Response({"results": data}, status=status.HTTP_200_OK)


# ============================
#     ScholarshipViewSet
# ============================

class ScholarshipViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:     GET /scholarships/        → список грантов (фильтры, поиск, сортировка)
    retrieve: GET /scholarships/{pk}/   → детальная инфо о гранте

    autocomplete: GET /scholarships/autocomplete/?q=<строка>
    """
    queryset = Scholarship.objects.all()

    # Возвращаем ваш FilterSet
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ScholarshipFilter
    search_fields   = ["name", "country"]
    ordering_fields = ["amount", "name", "deadline"]
    ordering = ["deadline"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ScholarshipDetailSerializer
        return ScholarshipMiniSerializer

    @action(detail=False, methods=["get"])
    def autocomplete(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"results": []})
        matches = Scholarship.objects.filter(name__icontains=q)[:10]
        data = [
            {"id": sch.id, "name": sch.name, "amount": sch.amount, "currency": sch.currency}
            for sch in matches
        ]
        return Response({"results": data}, status=status.HTTP_200_OK)


# ============================
#  UniversityFavoriteViewSet
# ============================

class UniversityFavoriteViewSet(
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        mixins.DestroyModelMixin,
        viewsets.GenericViewSet):
    serializer_class   = UniversityFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    filter_backends   = [DjangoFilterBackend, OrderingFilter]
    filterset_fields  = ["status", "pinned"]
    ordering_fields   = [
        "university__name",
        "order",
        "pinned",
        "status",
        "created_at",
    ]
    ordering = ["-pinned", "order"]

    def get_queryset(self):
        return UniversityFavorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if "order" not in serializer.validated_data:
            last = UniversityFavorite.objects.filter(user=self.request.user).order_by("-order").first()
            serializer.save(user=self.request.user, order=(last.order + 1) if last else 0)
        else:
            serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        data = request.data
        for item in data:
            fav_id   = item.get("id")
            new_order = item.get("order")
            if fav_id is None or new_order is None:
                continue
            try:
                fav = UniversityFavorite.objects.get(id=fav_id, user=request.user)
                fav.order = new_order
                fav.save(update_fields=["order"])
            except UniversityFavorite.DoesNotExist:
                continue
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================
#  ProgramFavoriteViewSet
# ============================

class ProgramFavoriteViewSet(
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        mixins.DestroyModelMixin,
        viewsets.GenericViewSet):
    serializer_class   = ProgramFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    filter_backends   = [DjangoFilterBackend, OrderingFilter]
    filterset_fields  = ["status", "pinned"]
    ordering_fields   = [
        "program__name",
        "program__deadline",
        "order",
        "pinned",
        "status",
        "created_at",
    ]
    ordering = ["-pinned", "order"]

    def get_queryset(self):
        return ProgramFavorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if "order" not in serializer.validated_data:
            last = ProgramFavorite.objects.filter(user=self.request.user).order_by("-order").first()
            serializer.save(user=self.request.user, order=(last.order + 1) if last else 0)
        else:
            serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        data = request.data
        for item in data:
            fav_id   = item.get("id")
            new_order = item.get("order")
            if fav_id is None or new_order is None:
                continue
            try:
                fav = ProgramFavorite.objects.get(id=fav_id, user=request.user)
                fav.order = new_order
                fav.save(update_fields=["order"])
            except ProgramFavorite.DoesNotExist:
                continue
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================
#  ScholarshipFavoriteViewSet
# ============================

class ScholarshipFavoriteViewSet(
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        mixins.DestroyModelMixin,
        viewsets.GenericViewSet):
    serializer_class   = ScholarshipFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    filter_backends   = [DjangoFilterBackend, OrderingFilter]
    filterset_fields  = ["status", "pinned"]
    ordering_fields   = [
        "scholarship__name",
        "scholarship__deadline",
        "order",
        "pinned",
        "status",
        "created_at",
    ]
    ordering = ["-pinned", "order"]

    def get_queryset(self):
        return ScholarshipFavorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if "order" not in serializer.validated_data:
            last = ScholarshipFavorite.objects.filter(user=self.request.user).order_by("-order").first()
            serializer.save(user=self.request.user, order=(last.order + 1) if last else 0)
        else:
            serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        data = request.data
        for item in data:
            fav_id   = item.get("id")
            new_order = item.get("order")
            if fav_id is None or new_order is None:
                continue
            try:
                fav = ScholarshipFavorite.objects.get(id=fav_id, user=request.user)
                fav.order = new_order
                fav.save(update_fields=["order"])
            except ScholarshipFavorite.DoesNotExist:
                continue
        return Response(status=status.HTTP_204_NO_CONTENT)
