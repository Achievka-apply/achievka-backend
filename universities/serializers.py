# universities/serializers.py

from rest_framework import serializers
from .models import (
    University,
    Program,
    Scholarship,
    UniversityFavorite,
    ProgramFavorite,
    ScholarshipFavorite
)
from datetime import date

# -----------------------------
# Mini‐сериализаторы для списков карточек
# -----------------------------

class UniversityMiniSerializer(serializers.ModelSerializer):
    programCount     = serializers.IntegerField(source="programs.count", read_only=True)
    scholarshipCount = serializers.IntegerField(source="scholarships.count", read_only=True)

    class Meta:
        model  = University
        fields = [
            "id",
            "name",
            "city",
            "country",
            "description",
            "study_format",
            "programCount",
            "scholarshipCount",
            "logo",
        ]


class ProgramMiniSerializer(serializers.ModelSerializer):
    university     = serializers.SerializerMethodField()
    hasScholarship = serializers.SerializerMethodField()

    def get_university(self, obj):
        return {
            "id": str(obj.university.id),
            "name": obj.university.name
        }

    def get_hasScholarship(self, obj):
        return "Yes" if obj.scholarships.exists() else "No"

    class Meta:
        model  = Program
        fields = [
            "id",
            "name",
            "study_type",
            "study_format",
            "city",
            "country",
            "tuition_fee",
            "duration",
            "rating",
            "deadline",
            "hasScholarship",
            "university",
        ]


class ScholarshipMiniSerializer(serializers.ModelSerializer):
    universities = serializers.SerializerMethodField()
    def get_universities(self, obj):

        return [
                        {"id": str(u.id), "name": u.name}
             for u in obj.universities.all()
            ]
    class Meta:
        model  = Scholarship
        fields = [
            "id",
            "name",
            "country",
            "amount",
            "currency",
            "deadline",
            "result_date",
            "min_ielts",
            "min_toefl",
            "min_sat",
            "min_act",
            "universities",
        ]


# -----------------------------
# Detail‐сериализаторы для страниц
# -----------------------------

class ProgramMiniInUniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = [
            "id",
            "name",
            "study_type",
            "tuition_fee",
            "duration",
            "deadline",
        ]


class UniversityDetailSerializer(serializers.ModelSerializer):
    programs         = ProgramMiniInUniSerializer(many=True, read_only=True)
    scholarshipCount = serializers.IntegerField(source="scholarships.count", read_only=True)

    class Meta:
        model  = University
        fields = [
            "id",
            "name",
            "description",
            "country",
            "city",
            "study_format",
            "programs",
            "scholarshipCount",
            "logo",
        ]


class UniversityMiniInProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = [
            "id",
            "name",
            "city",
            "country",
            "logo",
        ]


class ScholarshipMiniInProgramSerializer(serializers.ModelSerializer):
    """
    Мини‐сериализатор Scholarship для вложения в ProgramDetailSerializer.
    """
    class Meta:
        model = Scholarship
        fields = [
            "id",
            "name",
            "amount",
            "currency",
            "deadline",
        ]


class ProgramDetailSerializer(serializers.ModelSerializer):
    """
    Детальный сериализатор Program:
    - hasScholarship: "Yes" или "No"
    - days_left: "X days left"/"Deadline passed"/"Deadline: YYYY-MM-DD (est.)"
    - exams: требования (IELTS, TOEFL, SAT, ACT, GPA, IB, Cambridge)
    - official_link: URL
    - scholarships: список связанных грантов (через ScholarshipMiniInProgramSerializer)
    """
    university     = UniversityMiniInProgramSerializer(read_only=True)
    hasScholarship = serializers.SerializerMethodField()
    days_left      = serializers.SerializerMethodField()
    exams          = serializers.SerializerMethodField()
    official_link  = serializers.CharField(read_only=True)
    scholarships   = ScholarshipMiniInProgramSerializer(many=True, read_only=True)

    def get_hasScholarship(self, obj):
        return "Yes" if obj.scholarships.exists() else "No"

    def get_days_left(self, obj):
        if not obj.deadline:
            return None
        delta = (obj.deadline - date.today()).days
        if delta < 0:
            return f"Deadline passed: {obj.deadline.isoformat()}"
        if delta <= 30:
            return f"{delta} days left"
        return f"Deadline: {obj.deadline.isoformat()} (est.)"

    def get_exams(self, obj):
        result = {}
        if obj.min_ielts:
            result["IELTS"] = obj.min_ielts
        if obj.min_toefl:
            result["TOEFL"] = obj.min_toefl
        if obj.min_sat:
            result["SAT"] = obj.min_sat
        if obj.min_act:
            result["ACT"] = obj.min_act
        if obj.min_gpa is not None:
            result["GPA"] = str(obj.min_gpa)
        if obj.min_ib:
            result["IB Diploma"] = obj.min_ib
        if obj.min_cambridge:
            result["Cambridge Exam"] = obj.min_cambridge
        return result if result else None

    class Meta:
        model  = Program
        fields = [
            "id",
            "name",
            "description",
            "university",
            "city",
            "country",
            "study_format",
            "study_type",
            "duration",
            "tuition_fee",
            "rating",
            "deadline",
            "days_left",
            "hasScholarship",
            "exams",
            "official_link",
            "scholarships",
        ]


class ProgramMiniInScholarshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = [
            "id",
            "name",
            "study_type",
            "tuition_fee",
        ]


class UniversityMiniInScholarshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = [
            "id",
            "name",
            "city",
            "country",
            "logo",
        ]


class ScholarshipDetailSerializer(serializers.ModelSerializer):
    universities = UniversityMiniSerializer(many=True)
    programs = ProgramMiniInScholarshipSerializer(many=True, read_only=True)

    class Meta:
        model  = Scholarship
        fields = [
            "id",
            "name",
            "description",
            "official_link",
            "amount",
            "currency",
            "deadline",
            "result_date",
            "min_ielts",
            "min_toefl",
            "min_sat",
            "min_act",
            "extra_requirements",
            "programs",
            "universities",
        ]


# -----------------------------
# Сериализаторы избранного
# -----------------------------

class UniversityFavoriteSerializer(serializers.ModelSerializer):
    university    = UniversityMiniSerializer(read_only=True)
    university_id = serializers.PrimaryKeyRelatedField(
        queryset=University.objects.all(),
        source="university",
        write_only=True
    )

    class Meta:
        model  = UniversityFavorite
        fields = ["id", "university", "university_id", "created_at"]


class ProgramFavoriteSerializer(serializers.ModelSerializer):
    program    = ProgramMiniSerializer(read_only=True)
    program_id = serializers.PrimaryKeyRelatedField(
        queryset=Program.objects.all(),
        source="program",
        write_only=True
    )

    class Meta:
        model  = ProgramFavorite
        fields = ["id", "program", "program_id", "created_at"]


class ScholarshipFavoriteSerializer(serializers.ModelSerializer):
    scholarship    = ScholarshipMiniSerializer(read_only=True)
    scholarship_id = serializers.PrimaryKeyRelatedField(
        queryset=Scholarship.objects.all(),
        source="scholarship",
        write_only=True
    )

    class Meta:
        model  = ScholarshipFavorite
        fields = ["id", "scholarship", "scholarship_id", "created_at"]
