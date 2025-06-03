from django.db.models import Count
from django_filters import rest_framework as filters
from .models import University, Program, Scholarship

class UniversityFilter(filters.FilterSet):
    """
    1) Поиск (частичное совпадение по имени) → ?name=<строка>
    2) Фильтр по списку стран → ?countries=USA,Canada,Russia
    3) Фильтр по списку городов  → ?cities=London,Astana,Paris
    4) Фильтр по формату (online/campus/hybrid) → ?studyFormat=online
    5) Фильтр «hasScholarship» → ?hasScholarship=True/False
    """
    name           = filters.CharFilter(field_name="name", lookup_expr="icontains")
    countries      = filters.BaseInFilter(field_name="country", lookup_expr="in")
    cities         = filters.BaseInFilter(field_name="city", lookup_expr="in")
    studyFormat    = filters.CharFilter(field_name="study_format", lookup_expr="exact")
    hasScholarship = filters.BooleanFilter(method="filter_has_scholarship")

    def filter_has_scholarship(self, queryset, name, value):
        """
        Если value=True, возвращаем университеты, у которых есть хотя бы одна программа с грантом.
        Если value=False, — университеты, у которых ни одна программа не участвует ни в одном гранте.
        """
        if value:
            # Любые университеты, у которых есть связанный Scholarship через programs__scholarships
            return queryset.filter(programs__scholarships__isnull=False).distinct()
        else:
            # Университеты, у которых нет ни одного Scholarship через программы:
            # то есть исключаем те, кто имеет хотя бы один грант
            return queryset.exclude(programs__scholarships__isnull=False)

    class Meta:
        model  = University
        fields = [
            "name",
            "countries",
            "cities",
            "studyFormat",
            "hasScholarship",
        ]


class ProgramFilter(filters.FilterSet):
    """
    1) Поиск по названию → ?name=<строка>
    2) Фильтр по стране → ?country=<строка>
    3) Фильтр по городу  → ?city=<строка>
    4) Диапазон стоимости → ?tuitionMin=<число>&tuitionMax=<число>
    5) Фильтр по продолжительности → ?duration=<строка>
    6) Фильтр по формату → ?studyFormat=online
    7) Фильтр по типу   → ?studyType=full-time
    8) Даты дедлайнов   → ?deadlineFrom=2025-06-01&deadlineTo=2025-12-31
    9) Фильтр hasScholarship → ?hasScholarship=True/False
    10) Sorting (осуществляется не здесь, а в ViewSet через OrderingFilter)
    """
    name           = filters.CharFilter(field_name="name", lookup_expr="icontains")
    country        = filters.CharFilter(field_name="country", lookup_expr="icontains")
    city           = filters.CharFilter(field_name="city", lookup_expr="icontains")
    tuitionMin     = filters.NumberFilter(field_name="tuition_fee", lookup_expr="gte")
    tuitionMax     = filters.NumberFilter(field_name="tuition_fee", lookup_expr="lte")
    duration       = filters.CharFilter(field_name="duration", lookup_expr="icontains")
    studyFormat    = filters.CharFilter(field_name="study_format", lookup_expr="exact")
    studyType      = filters.CharFilter(field_name="study_type", lookup_expr="exact")
    deadlineFrom   = filters.DateFilter(field_name="deadline", lookup_expr="gte")
    deadlineTo     = filters.DateFilter(field_name="deadline", lookup_expr="lte")
    hasScholarship = filters.BooleanFilter(method="filter_has_scholarship")

    def filter_has_scholarship(self, queryset, name, value):
        """
        Если value=True, оставляем только программы, у которых есть хотя бы один связанный Scholarship.
        Если False, — только те, у которых нет ни одного гранта.
        """
        if value:
            return queryset.filter(scholarships__isnull=False).distinct()
        else:
            return queryset.filter(scholarships__isnull=True)

    class Meta:
        model  = Program
        fields = [
            "name",
            "country",
            "city",
            "tuitionMin",
            "tuitionMax",
            "duration",
            "studyFormat",
            "studyType",
            "deadlineFrom",
            "deadlineTo",
            "hasScholarship",
        ]


class ScholarshipFilter(filters.FilterSet):
    """
    1) Диапазон по сумме → ?amountMin=<число>&amountMax=<число>
    2) Даты дедлайна (от/до) → ?submissionDeadlineFrom=2025-06-01&submissionDeadlineTo=2025-12-31
    3) Фильтр hasResultDate (есть ли result_date) → ?hasResultDate=True/False
    4) Минимальные требования по экзаменам →
         ?minIELTS=<строка>&minTOEFL=<строка>&minSAT=<строка>&minACT=<строка>
    """
    amountMin              = filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amountMax              = filters.NumberFilter(field_name="amount", lookup_expr="lte")
    submissionDeadlineFrom = filters.DateFilter(field_name="deadline", lookup_expr="gte")
    submissionDeadlineTo   = filters.DateFilter(field_name="deadline", lookup_expr="lte")
    # Если hasResultDate=True, хотим только те, у которых result_date НЕ NULL
    # Для BooleanFilter указываем lookup_expr="isnull" и exclude=True,
    #  чтобы фактически он работал как «NOT isnull» при True
    hasResultDate          = filters.BooleanFilter(
        field_name="result_date", lookup_expr="isnull", exclude=True
    )
    minIELTS               = filters.CharFilter(field_name="min_ielts", lookup_expr="gte")
    minTOEFL               = filters.CharFilter(field_name="min_toefl", lookup_expr="gte")
    minSAT                 = filters.CharFilter(field_name="min_sat", lookup_expr="gte")
    minACT                 = filters.CharFilter(field_name="min_act", lookup_expr="gte")

    class Meta:
        model  = Scholarship
        fields = [
            "amountMin",
            "amountMax",
            "submissionDeadlineFrom",
            "submissionDeadlineTo",
            "hasResultDate",
            "minIELTS",
            "minTOEFL",
            "minSAT",
            "minACT",
        ]
