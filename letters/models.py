import uuid
from django.conf import settings
from django.db import models

LETTER_TYPES = [
    ('motivation', 'Motivation Letter'),
    ('common_app', 'Common App Essay'),
    ('ucas', 'UCAS Essay'),
]
STATUS_CHOICES = [
    ('draft', 'Черновик'),
    ('generated', 'Сгенерирована'),
    ('locked', 'Нужна подписка'),
]

class Letter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='letters'
    )
    name = models.CharField(max_length=255)  # произвольное имя письма
    type = models.CharField(max_length=20, choices=LETTER_TYPES)
    # Поля, специфичные для разных типов писем:
    program = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Для motivation и ucas'
    )
    university = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Только для motivation'
    )
    essay_prompt = models.TextField(
        blank=True,
        null=True,
        help_text='Только для common_app'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Статус проверки письма'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class LetterVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    letter = models.ForeignKey(
        Letter,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_num = models.IntegerField()
    s3_key = models.CharField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)
    checked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('letter', 'version_num')
        ordering = ['version_num']

    def __str__(self):
        return f"{self.letter.name} – v{self.version_num}"

class VersionMessage(models.Model):
    """
    Хранит последовательность сообщений (system/user/assistant)
    для каждой версии письма.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(
        LetterVersion,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(
        max_length=20,
        choices=[('system','system'), ('user','user'), ('assistant','assistant')]
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

class DraftLetter(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    on_delete=models.CASCADE,
                                    related_name='draft_letters')
    name        = models.CharField(max_length=255)
    type        = models.CharField(max_length=20, choices=LETTER_TYPES)
    program     = models.CharField(max_length=255)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class DraftAnswer(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    draft_letter  = models.ForeignKey(DraftLetter,
                                      on_delete=models.CASCADE,
                                      related_name='answers')
    question_key  = models.CharField(max_length=100)
    answer_text   = models.TextField(blank=True)
    order         = models.PositiveIntegerField()
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']


class DraftSection(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    draft_letter  = models.ForeignKey(DraftLetter,
                                      on_delete=models.CASCADE,
                                      related_name='sections')
    section_key   = models.CharField(max_length=50)
    prompt_hint   = models.TextField()
    tone_style    = models.TextField()
    user_text     = models.TextField(blank=True)
    order         = models.PositiveIntegerField()
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']