#universities/filters.py
from django.db.models import Count
from django_filters import rest_framework as filters
from .models import University, Program, Scholarship

class UniversityFilter(filters.FilterSet):
    name           = filters.CharFilter(field_name="name", lookup_expr="icontains")
    countries      = filters.BaseInFilter(field_name="country", lookup_expr="in")
    cities         = filters.BaseInFilter(field_name="city", lookup_expr="in")
    studyFormat    = filters.CharFilter(field_name="study_format")
    hasScholarship = filters.BooleanFilter(method="filter_has_scholarship")

    def filter_has_scholarship(self, qs, name, value):
        return qs.annotate(
            cnt=Count("scholarship")
        ).filter(cnt__gt=0 if value else 0)

    class Meta:
        model  = University
        fields = ["name","countries","cities","studyFormat","hasScholarship"]


class ProgramFilter(filters.FilterSet):
    name            = filters.CharFilter(field_name="name", lookup_expr="icontains")
    country         = filters.CharFilter(field_name="country")
    city            = filters.CharFilter(field_name="city")
    tuitionMin      = filters.NumberFilter(field_name="tuition_fee", lookup_expr="gte")
    tuitionMax      = filters.NumberFilter(field_name="tuition_fee", lookup_expr="lte")
    duration        = filters.CharFilter(field_name="duration")
    studyFormat     = filters.CharFilter(field_name="study_format")
    studyType       = filters.CharFilter(field_name="study_type")
    deadlineFrom    = filters.DateFilter(field_name="deadline", lookup_expr="gte")
    deadlineTo      = filters.DateFilter(field_name="deadline", lookup_expr="lte")
    hasScholarship  = filters.BooleanFilter(method="filter_has_scholarship")
    sortBy          = filters.OrderingFilter(
        fields=(("tuition_fee","tuition_fee"),("deadline","deadline"))
    )

    def filter_has_scholarship(self, qs, name, value):
        return qs.filter(scholarship__isnull=(not value))

    class Meta:
        model  = Program
        fields = ["name","country","city","tuitionMin","tuitionMax",
                  "duration","studyFormat","studyType","deadlineFrom","deadlineTo","hasScholarship"]


class ScholarshipFilter(filters.FilterSet):
    amountMin             = filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amountMax             = filters.NumberFilter(field_name="amount", lookup_expr="lte")
    submissionDeadlineFrom= filters.DateFilter(field_name="deadline", lookup_expr="gte")
    submissionDeadlineTo  = filters.DateFilter(field_name="deadline", lookup_expr="lte")
    hasResultDate         = filters.BooleanFilter(field_name="result_date", lookup_expr="isnull", exclude=True)
    minIELTS              = filters.CharFilter(field_name="min_ielts", lookup_expr="gte")
    minTOEFL              = filters.CharFilter(field_name="min_toefl", lookup_expr="gte")
    minSAT                = filters.CharFilter(field_name="min_sat", lookup_expr="gte")
    minACT                = filters.CharFilter(field_name="min_act", lookup_expr="gte")

    class Meta:
        model  = Scholarship
        fields = ["amountMin","amountMax","submissionDeadlineFrom",
                  "submissionDeadlineTo","hasResultDate","minIELTS","minTOEFL","minSAT","minACT"]
