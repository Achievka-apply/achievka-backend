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
    programCount = serializers.IntegerField(source="programs.count", read_only=True)
    scholarshipCount = serializers.IntegerField(source="scholarships.count", read_only=True)

    class Meta:
        model = University
        fields = [
            "id",
            "name",
            "city",
            "country",
            "description",
            "study_format",
            "programCount",
            "scholarshipCount",
        ]


class ProgramMiniSerializer(serializers.ModelSerializer):
    university = serializers.SerializerMethodField()
    hasScholarship = serializers.SerializerMethodField()

    def get_university(self, obj):
        return {
            "id": str(obj.university.id),
            "name": obj.university.name
        }

    def get_hasScholarship(self, obj):
        # Возвращаем "Yes" или "No"
        return "Yes" if obj.scholarships.exists() else "No"

    class Meta:
        model = Program
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
    university = serializers.SerializerMethodField()

    def get_university(self, obj):
        return {
            "id": str(obj.university.id),
            "name": obj.university.name
        }

    class Meta:
        model = Scholarship
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
            "university",
        ]


# -----------------------------
# Detail‐сериализаторы для страниц
# -----------------------------

class ProgramMiniInUniSerializer(serializers.ModelSerializer):
    """
    Вложенный мини‐сериализатор Program (для UniversityDetailSerializer).
    """

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
    """
    Детальный сериализатор University:
    – список программ (через ProgramMiniInUniSerializer),
    – количество грантов.
    """
    programs = ProgramMiniInUniSerializer(many=True, read_only=True)
    scholarshipCount = serializers.IntegerField(source="scholarships.count", read_only=True)

    class Meta:
        model = University
        fields = [
            "id",
            "name",
            "description",
            "country",
            "city",
            "study_format",
            "programs",
            "scholarshipCount",
        ]


class UniversityMiniInProgramSerializer(serializers.ModelSerializer):
    """
    Вложенный мини‐сериализатор University (для ProgramDetailSerializer).
    """

    class Meta:
        model = University
        fields = [
            "id",
            "name",
            "city",
            "country",
            "logo",
        ]


class ProgramDetailSerializer(serializers.ModelSerializer):
    """
    Детальный сериализатор Program.
    Добавлены:
    - hasScholarship: "Yes" или "No"
    - days_left: формат "X days left" или "Deadline passed"/"Deadline: YYYY-MM-DD (est.)"
    - exams: блок всех требований (IELTS, TOEFL, SAT, ACT, GPA, IB Diploma, Cambridge Exam)
    - official_link: ссылка на страницу программы
    """
    university = UniversityMiniInProgramSerializer(read_only=True)
    hasScholarship = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()
    exams = serializers.SerializerMethodField()
    official_link = serializers.CharField(read_only=True)

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
        """
        Собираем блок требований:
        - IELTS, TOEFL, SAT, ACT (CharField)
        - GPA (DecimalField)
        - IB Diploma (CharField)
        - Cambridge Exam (CharField)
        """
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
        model = Program
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
        ]


class ProgramMiniInScholarshipSerializer(serializers.ModelSerializer):
    """
    Вложенный мини‐сериализатор Program (для ScholarshipDetailSerializer).
    """

    class Meta:
        model = Program
        fields = [
            "id",
            "name",
            "study_type",
            "tuition_fee",
        ]


class ScholarshipDetailSerializer(serializers.ModelSerializer):
    """
    Детальный сериализатор Scholarship:
    – вложенный UniversityMiniSerializer,
    – вложенный список ProgramMiniInScholarshipSerializer,
    – минимальные требования (min_ielts, min_toefl и т. д.).
    """
    university = UniversityMiniSerializer(read_only=True)
    programs = ProgramMiniInScholarshipSerializer(many=True, read_only=True)

    class Meta:
        model = Scholarship
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
            "university",
            "programs",
        ]


# -----------------------------
# Сериализаторы избранного (не изменились)
# -----------------------------

class UniversityFavoriteSerializer(serializers.ModelSerializer):
    university = UniversityMiniSerializer(read_only=True)
    university_id = serializers.PrimaryKeyRelatedField(
        queryset=University.objects.all(),
        source="university",
        write_only=True
    )

    class Meta:
        model = UniversityFavorite
        fields = ["id", "university", "university_id", "created_at"]


class ProgramFavoriteSerializer(serializers.ModelSerializer):
    program = ProgramMiniSerializer(read_only=True)
    program_id = serializers.PrimaryKeyRelatedField(
        queryset=Program.objects.all(),
        source="program",
        write_only=True
    )

    class Meta:
        model = ProgramFavorite
        fields = ["id", "program", "program_id", "created_at"]


class ScholarshipFavoriteSerializer(serializers.ModelSerializer):
    scholarship = ScholarshipMiniSerializer(read_only=True)
    scholarship_id = serializers.PrimaryKeyRelatedField(
        queryset=Scholarship.objects.all(),
        source="scholarship",
        write_only=True
    )

    class Meta:
        model = ScholarshipFavorite
        fields = ["id", "scholarship", "scholarship_id", "created_at"]
