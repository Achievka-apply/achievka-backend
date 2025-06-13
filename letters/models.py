import uuid
from django.conf import settings
from django.db import models

LETTER_TYPES = [
    ('motivation', 'Motivation Letter'),
    ('common_app', 'Common App Essay'),
    ('ucas', 'UCAS Essay'),
]

class Letter(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   related_name='letters')
    name       = models.CharField(max_length=255)  # произвольное имя письма
    type       = models.CharField(max_length=20, choices=LETTER_TYPES)
    program    = models.CharField(max_length=255)  # или FK на модель Program
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class LetterVersion(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    letter      = models.ForeignKey(Letter,
                                    on_delete=models.CASCADE,
                                    related_name='versions')
    version_num = models.IntegerField()
    s3_key      = models.CharField(max_length=1024)
    created_at  = models.DateTimeField(auto_now_add=True)
    checked_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('letter', 'version_num')
        ordering = ['version_num']

    def __str__(self):
        return f"{self.letter.name} – v{self.version_num}"
