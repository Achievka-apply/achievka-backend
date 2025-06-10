from django.db.models import Count
from django_filters import rest_framework as filters
from .models import University, Program, Scholarship
# universities/filters.py
from django.db.models.functions import Cast
from django.db.models import IntegerField
from django_filters import rest_framework as filters
from .models import University

class UniversityFilter(filters.FilterSet):
    """
    1) Поиск (частичное совпадение по имени) → ?name=<строка>
    2) Фильтр по списку стран → ?countries=USA,Canada,Russia
    3) Фильтр по списку городов  → ?cities=London,Astana,Paris
    4) Фильтр по формату (online/campus/hybrid) → ?studyFormat=online
    5) Фильтр «hasScholarship» → ?hasScholarship=True/False
       (только прямая связь University.scholarships)
    """
    name           = filters.CharFilter(field_name="name", lookup_expr="icontains")
    countries      = filters.BaseInFilter(field_name="country", lookup_expr="in")
    cities         = filters.BaseInFilter(field_name="city", lookup_expr="in")
    studyFormat    = filters.CharFilter(field_name="study_format", lookup_expr="exact")
    hasScholarship = filters.BooleanFilter(method="filter_has_scholarship")

    def filter_has_scholarship(self, queryset, name, value):
        """
        Если value=True, возвращаем университеты, у которых есть хотя бы один
        связанный Scholarship напрямую (через University.scholarships).
        Если value=False, возвращаем университеты, у которых нет ни одного
        прямого Scholarship.
        """
        if value:
            return queryset.filter(scholarships__isnull=False).distinct()
        else:
            return queryset.filter(scholarships__isnull=True)

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
    minIELTS  = filters.NumberFilter(method="filter_ielts_range")
    maxIELTS  = filters.NumberFilter(method="filter_ielts_range")
    minTOEFL  = filters.NumberFilter(method="filter_toefl_range")
    maxTOEFL  = filters.NumberFilter(method="filter_toefl_range")
    minSAT    = filters.NumberFilter(method="filter_sat_range")
    maxSAT    = filters.NumberFilter(method="filter_sat_range")
    minACT    = filters.NumberFilter(method="filter_act_range")
    maxACT    = filters.NumberFilter(method="filter_act_range")

    def filter_ielts_range(self, qs, name, value):
        qs = qs.exclude(min_ielts__exact="")
        qs = qs.annotate(ielts_val=Cast("min_ielts", IntegerField()))
        return qs.filter(**{"ielts_val__gte" if name=="minIELTS" else "ielts_val__lte": value})

    def filter_toefl_range(self, qs, name, value):
        qs = qs.exclude(min_toefl__exact="")
        qs = qs.annotate(toefl_val=Cast("min_toefl", IntegerField()))
        return qs.filter(**{"toefl_val__gte" if name=="minTOEFL" else "toefl_val__lte": value})

    def filter_act_range(self, qs, name, value):
        qs = qs.exclude(min_act__exact="")
        qs = qs.annotate(act_val=Cast("min_act", IntegerField()))
        return qs.filter(**{"act_val__gte" if name=="minACT" else "act_val__lte": value})


    def filter_has_scholarship(self, queryset, name, value):
        """
        Если value=True, оставляем только программы, у которых есть хотя бы один связанный Schol`arship.
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
            "minIELTS",
            "maxIELTS",
            "minTOEFL",
            "maxTOEFL",
            "minSAT",
            "maxSAT",
            "minACT",
            "maxACT",
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
    minIELTS  = filters.NumberFilter(method="filter_ielts_range")
    maxIELTS  = filters.NumberFilter(method="filter_ielts_range")
    minTOEFL  = filters.NumberFilter(method="filter_toefl_range")
    maxTOEFL  = filters.NumberFilter(method="filter_toefl_range")
    minSAT    = filters.NumberFilter(method="filter_sat_range")
    maxSAT    = filters.NumberFilter(method="filter_sat_range")
    minACT    = filters.NumberFilter(method="filter_act_range")
    maxACT    = filters.NumberFilter(method="filter_act_range")

    def filter_ielts_range(self, qs, name, value):
        qs = qs.exclude(min_ielts__exact="")
        qs = qs.annotate(ielts_val=Cast("min_ielts", IntegerField()))
        return qs.filter(**{"ielts_val__gte" if name=="minIELTS" else "ielts_val__lte": value})

    def filter_toefl_range(self, qs, name, value):
        qs = qs.exclude(min_toefl__exact="")
        qs = qs.annotate(toefl_val=Cast("min_toefl", IntegerField()))
        return qs.filter(**{"toefl_val__gte" if name=="minTOEFL" else "toefl_val__lte": value})

    def filter_act_range(self, qs, name, value):
        qs = qs.exclude(min_act__exact="")
        qs = qs.annotate(act_val=Cast("min_act", IntegerField()))
        return qs.filter(**{"act_val__gte" if name=="minACT" else "act_val__lte": value})


    class Meta:
        model  = Scholarship
        fields = [
            "amountMin",
            "amountMax",
            "submissionDeadlineFrom",
            "submissionDeadlineTo",
            "hasResultDate",
            "minIELTS",
            "maxIELTS",
            "minTOEFL",
            "maxTOEFL",
            "minSAT",
            "maxSAT",
            "minACT",
            "maxACT",
        ]
