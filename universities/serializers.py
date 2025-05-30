#universities/serializers.py
from rest_framework import serializers
from .models import (
    University, Program, Scholarship,
    UniversityFavorite, ProgramFavorite, ScholarshipFavorite
)
from datetime import date

# — Mini‐сериализаторы для списков карточек —

class UniversityMiniSerializer(serializers.ModelSerializer):
    programCount     = serializers.IntegerField(source="programs.count", read_only=True)
    scholarshipCount = serializers.IntegerField(source="scholarships.count", read_only=True)

    class Meta:
        model  = University
        fields = ["id","name","city","country","description",
                  "programCount","scholarshipCount","study_format"]


class ProgramMiniSerializer(serializers.ModelSerializer):
    university     = serializers.SerializerMethodField()
    hasScholarship = serializers.BooleanField(source="scholarships.exists", read_only=True)

    def get_university(self, obj):
        return {"id": str(obj.university.id), "name": obj.university.name}

    class Meta:
        model  = Program
        fields = ["id","name","study_type","study_format",
                  "city","country","tuition_fee","duration",
                  "rating","deadline","hasScholarship","university"]


class ScholarshipMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Scholarship
        fields = ["id","name","country","amount","currency",
                  "deadline","description","result_date",
                  "min_ielts","min_toefl","min_sat","min_act"]


# — Detail‐сериализаторы для страниц 5/6/7 —

class UniversityDetailSerializer(serializers.ModelSerializer):
    scholarships = serializers.StringRelatedField(many=True, source="scholarships")

    class Meta:
        model  = University
        fields = ["id","name","country","city","description",
                  "study_format","scholarships"]


class ProgramDetailSerializer(serializers.ModelSerializer):
    university   = UniversityMiniSerializer(read_only=True)
    days_left    = serializers.SerializerMethodField()
    hasScholarship = serializers.BooleanField(source="scholarships.exists", read_only=True)

    def get_days_left(self, obj):
        if not obj.deadline:
            return None
        delta = (obj.deadline - date.today()).days
        if 0 <= delta <= 30:
            return f"{delta} days left"
        return f"Deadline: {obj.deadline.isoformat()} (est.)"

    class Meta:
        model  = Program
        fields = ["id","name","description","university","city","country",
                  "study_format","study_type","duration","tuition_fee",
                  "hasScholarship","deadline","days_left"]


class ScholarshipDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Scholarship
        fields = ["id","name","country","amount","currency","deadline",
                  "result_date","description","min_ielts","min_toefl",
                  "min_sat","min_act"]


# — Сериализаторы избранного —

class UniversityFavoriteSerializer(serializers.ModelSerializer):
    university    = UniversityMiniSerializer(read_only=True)
    university_id = serializers.PrimaryKeyRelatedField(
        queryset=University.objects.all(),
        source="university", write_only=True
    )

    class Meta:
        model  = UniversityFavorite
        fields = ["id","university","university_id","created_at"]


class ProgramFavoriteSerializer(serializers.ModelSerializer):
    program    = ProgramMiniSerializer(read_only=True)
    program_id = serializers.PrimaryKeyRelatedField(
        queryset=Program.objects.all(),
        source="program", write_only=True
    )

    class Meta:
        model  = ProgramFavorite
        fields = ["id","program","program_id","created_at"]


class ScholarshipFavoriteSerializer(serializers.ModelSerializer):
    scholarship    = ScholarshipMiniSerializer(read_only=True)
    scholarship_id = serializers.PrimaryKeyRelatedField(
        queryset=Scholarship.objects.all(),
        source="scholarship", write_only=True
    )

    class Meta:
        model  = ScholarshipFavorite
        fields = ["id","scholarship","scholarship_id","created_at"]
