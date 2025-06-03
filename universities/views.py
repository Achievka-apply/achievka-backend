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


# Права доступа: только владелец может удалять свой favorite
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


# ============================
#      UniversityViewSet
# ============================

class UniversityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:     GET /universities/             → возвращает список университетов, с фильтрами, поиском, сортировкой
    retrieve: GET /universities/{pk}/        → детальная информация об университете

    Дополнительно:
    autocomplete: GET /universities/autocomplete/?q=<префикс>
        → возвращает до 10 совпадений по name для автоподсказок
    """
    # 1) queryset здесь мы сразу аннотируем двумя дополнительными полями:
    #    a) count_programs — число закреплённых программ у данного университета
    #    b) min_program_fee — минимальная tuition_fee среди всех программ этого университета
    queryset = University.objects.annotate(
        count_programs=Count("programs", distinct=True),
        min_program_fee=Min("programs__tuition_fee")
    ).all()

    # 2) Подключаем фильтры, поиск и сортировку
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = UniversityFilter
    search_fields   = ["name", "city", "country"]
    # ordering_fields указываем, какие поля можно передавать в ?ordering=<поле>
    ordering_fields = [
        "name",             # алфавит (A-Z или Z-A)
        "min_program_fee",  # «цена» — минимальная стоимость программы
        "count_programs"    # например, по количеству программ (если когда-то нужно)
    ]
    # По умолчанию, если не указан ordering, отдаём по имени в алфавитном порядке
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UniversityDetailSerializer
        return UniversityMiniSerializer

    @action(detail=False, methods=["get"])
    def autocomplete(self, request):
        """
        GET /universities/autocomplete/?q=<строка>
        Возвращает до 10 университетов, у которых name начинается или содержит <строка> (regardless of case).
        """

        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"results": []})

        # Ищем первые 10 совпадений по частичному понятию (icontains);
        # можно заменить на startswith, если строго «начинается с».
        matches = University.objects.filter(name__icontains=q)[:10]
        # Сериализуем только поле id и name (можно сделать отдельный мини-сериализатор,
        # но для простоты вернём список dict)
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
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProgramFilter
    search_fields   = ["name", "university__name", "city", "country"]
    # Разрешаем сортировать по:
    #   1) tuition_fee — «цена»
    #   2) name        — «алфавит»
    #   3) deadline    — «дедлайн»
    ordering_fields = ["tuition_fee", "name", "deadline"]
    # По умолчанию сортируем по алфавиту
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProgramDetailSerializer
        return ProgramMiniSerializer

    @action(detail=False, methods=["get"])
    def autocomplete(self, request):
        """
        GET /programs/autocomplete/?q=<строка>
        Возвращает до 10 программ, у которых name содержит <строка>.
        """
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
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ScholarshipFilter
    search_fields   = ["name", "country"]
    # Сортировка по:
    #   1) amount   — «цена»
    #   2) name     — «алфавит»
    #   3) deadline — «дедлайн»
    ordering_fields = ["amount", "name", "deadline"]
    # По умолчанию сортируем по дедлайну (сначала самые близкие дедлайны)
    ordering = ["deadline"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ScholarshipDetailSerializer
        return ScholarshipMiniSerializer

    @action(detail=False, methods=["get"])
    def autocomplete(self, request):
        """
        GET /scholarships/autocomplete/?q=<строка>
        Возвращает до 10 грантов, у которых name содержит <строка>.
        """
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
#  Favorite ViewSets (unchanged)
# ============================

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
