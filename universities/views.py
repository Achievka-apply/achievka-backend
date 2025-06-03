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


# Права доступа: только владелец может удалять/обновлять свой favorite
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


# ============================
#      UniversityViewSet (без изменений)
# ============================

class UniversityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = University.objects.annotate(
        count_programs=Count("programs", distinct=True),
        min_program_fee=Min("programs__tuition_fee")
    ).all()

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = None  # сюда можно подключить UniversityFilter, если нужно
    search_fields   = ["name", "city", "country"]
    ordering_fields = ["name", "min_program_fee", "count_programs"]
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
#      ProgramViewSet (без изменений)
# ============================

class ProgramViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Program.objects.select_related("university").all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = None  # сюда можно подключить ProgramFilter, если нужно
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
#     ScholarshipViewSet (без изменений)
# ============================

class ScholarshipViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Scholarship.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = None  # сюда можно подключить ScholarshipFilter, если нужно
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

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "pinned"]  # фронт может ?status=ready_to_apply или ?pinned=True
    ordering_fields = [
        "university__name",   # сортировка по имени университета (алфавит)
        "order",              # собственный порядок
        "pinned",             # чтобы сгруппировать сначала закреплённые
        "status",             # чтобы, при необходимости, выбрать только по статусу
        "created_at",         # по дате добавления
    ]
    ordering = ["-pinned", "order"]  # по умолчанию сначала пины, затем пользовательский order

    def get_queryset(self):
        return UniversityFavorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Если фронт не передаёт order, можно автоматически присвоить max(order)+1
        if "order" not in serializer.validated_data:
            last = UniversityFavorite.objects.filter(user=self.request.user).order_by("-order").first()
            serializer.save(user=self.request.user, order=(last.order + 1) if last else 0)
        else:
            serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        """
        Массовое переупорядочивание: фронт присылает список объектов вида:
        [
          {"id": <favorite_id>, "order": <new_position>},
          ...
        ]
        """
        data = request.data
        for item in data:
            fav_id = item.get("id")
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
        "program__name",      # по имени программы
        "program__deadline",  # по дедлайну программы
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
        """
        Фронт посылает:
        [
          {"id": <favorite_id>, "order": <new_position>},
          ...
        ]
        """
        data = request.data
        for item in data:
            fav_id = item.get("id")
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
        "scholarship__name",      # по имени гранта
        "scholarship__deadline",  # по дедлайну гранта
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
        """
        Фронт посылает:
        [
          {"id": <favorite_id>, "order": <new_position>},
          ...
        ]
        """
        data = request.data
        for item in data:
            fav_id = item.get("id")
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
