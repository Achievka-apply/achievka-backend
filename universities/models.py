# universities/models.py

from django.conf import settings
from django.db import models

class University(models.Model):
    STUDY_FORMAT_CHOICES = [
        ("online", "Online"),
        ("campus", "On Campus"),
        ("hybrid", "Hybrid"),
    ]

    name         = models.CharField(max_length=255)
    country      = models.CharField(max_length=100)
    city         = models.CharField(max_length=100)
    description  = models.TextField(blank=True)
    study_format = models.CharField(max_length=10, choices=STUDY_FORMAT_CHOICES)

    # Новые поля:
    logo    = models.ImageField(
        upload_to="university_logos/",    # директория внутри MEDIA_ROOT
        null=True,
        blank=True,
        help_text="PNG-логотип университета"
    )
    website = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Официальный сайт университета"
    )

    def __str__(self):
        return self.name


class Program(models.Model):
    STUDY_TYPE_CHOICES = [
        ("part-time", "Part Time"),
        ("full-time", "Full Time"),
    ]

    STUDY_FORMAT_CHOICES = University.STUDY_FORMAT_CHOICES

    university    = models.ForeignKey(
        University,
        related_name="programs",
        on_delete=models.CASCADE
    )
    name          = models.CharField(max_length=255)
    description   = models.TextField(blank=True)

    study_type    = models.CharField(max_length=10, choices=STUDY_TYPE_CHOICES)
    study_format  = models.CharField(max_length=10, choices=STUDY_FORMAT_CHOICES)
    city          = models.CharField(max_length=100)
    country       = models.CharField(max_length=100)
    tuition_fee   = models.PositiveIntegerField()
    duration      = models.CharField(max_length=50, help_text="Например: '2 years'")
    rating        = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    deadline      = models.DateField(null=True, blank=True)

    # — Поля для требований/экзаменов —
    min_ielts     = models.CharField(max_length=10, blank=True, help_text="Минимальный балл IELTS (если есть)")
    min_toefl     = models.CharField(max_length=10, blank=True, help_text="Минимальный балл TOEFL (если есть)")
    min_sat       = models.CharField(max_length=10, blank=True, help_text="Минимальный балл SAT (если есть)")
    min_act       = models.CharField(max_length=10, blank=True, help_text="Минимальный балл ACT (если есть)")
    min_gpa       = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="Минимальный GPA (если есть)")
    min_ib        = models.CharField(max_length=20, blank=True, help_text="Требование по IB Diploma (например: 'Diploma required' или 'IB 30')")
    min_cambridge = models.CharField(max_length=20, blank=True, help_text="Требование по Cambridge Exam (например: 'Cambridge C1 Advanced')")

    # — Ссылка на официальную страницу программы —
    official_link = models.URLField(blank=True, help_text="URL официальной страницы программы")

    def __str__(self):
        return f"{self.name} @ {self.university.name}"


class Scholarship(models.Model):
    university    = models.ForeignKey(
        University,
        related_name="scholarships",
        on_delete=models.CASCADE
    )
    name          = models.CharField(max_length=255)
    country       = models.CharField(max_length=100)
    amount        = models.PositiveIntegerField()
    currency      = models.CharField(max_length=10, default="USD")
    deadline      = models.DateField()
    result_date   = models.DateField(null=True, blank=True)
    description   = models.TextField(blank=True)

    # — Минимальные требования/баллы для гранта —
    min_ielts     = models.CharField(max_length=10, blank=True, help_text="Минимальный балл IELTS (если есть)")
    min_toefl     = models.CharField(max_length=10, blank=True, help_text="Минимальный балл TOEFL (если есть)")
    min_sat       = models.CharField(max_length=10, blank=True, help_text="Минимальный балл SAT (если есть)")
    min_act       = models.CharField(max_length=10, blank=True, help_text="Минимальный балл ACT (если есть)")

    # — Ссылка на официальный сайт гранта —
    official_link = models.URLField(blank=True, help_text="URL официального сайта гранта")

    # — Связь ManyToMany: какие программы покрывает этот грант —
    programs      = models.ManyToManyField(
        Program,
        related_name="scholarships",
        blank=True,
        help_text="Программы, на которые распространяется этот грант"
    )

    def __str__(self):
        return self.name


# -----------------------
# МОДЕЛИ ИЗБРАННОГО
# -----------------------

class UniversityFavorite(models.Model):
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fav_universities"
    )
    university  = models.ForeignKey(University, on_delete=models.CASCADE)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "university")


class ProgramFavorite(models.Model):
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fav_programs"
    )
    program     = models.ForeignKey(Program, on_delete=models.CASCADE)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "program")


class ScholarshipFavorite(models.Model):
    user         = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fav_scholarships"
    )
    scholarship  = models.ForeignKey(Scholarship, on_delete=models.CASCADE)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "scholarship")
