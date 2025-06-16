# letters/views.py

import logging
import boto3
import json
import openai

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
#from openai.enums import ResponseFormat

from .models import Letter, LetterVersion, VersionMessage
from .serializers import LetterSerializer, LetterVersionSerializer
from .s3_utils import upload_letter_text

# Устанавливаем ключ OpenAI
openai.api_key = settings.OPENAI_API_KEY


class LetterViewSet(viewsets.ModelViewSet):
    """
    CRUD-эндпоинты для писем + версии + analyse
    с памятью и гейтингом по подписке (User.has_subscription).
    """
    queryset = Letter.objects.all()
    serializer_class = LetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Возвращаем только письма текущего пользователя
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # При создании письма фиксируем владельца
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get', 'post'], url_path='versions')
    def versions(self, request, pk=None):
        """
        GET  /api/letters/{id}/versions/  — список версий
        POST /api/letters/{id}/versions/ — сохраняет новую версию письма в S3
        """
        letter = self.get_object()

        if request.method == 'GET':
            qs = letter.versions.all()
            serializer = LetterVersionSerializer(qs, many=True)
            return Response(serializer.data)

        # POST → создать новую версию
        text     = request.data.get('text', '')
        autosave = request.data.get('autosave', True)

        # определяем следующий номер версии
        last = letter.versions.order_by('-version_num').first()
        next_num = (last.version_num + 1) if last else 1

        # сохраняем текст в S3
        s3_key = upload_letter_text(
            user_id=str(request.user.id),
            letter_id=str(letter.id),
            version_num=next_num,
            text=text
        )

        # создаём запись в БД
        version = LetterVersion.objects.create(
            letter=letter,
            version_num=next_num,
            s3_key=s3_key
        )

        serializer = LetterVersionSerializer(version)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['post'], url_path='analyse')
    def analyse(self, request, pk=None):
        """
        POST /api/letters/{id}/analyse/
        Сохраняет новую версию в S3 (автосохранение уже сделано) и
        возвращает полный JSON-ответ от OpenAI без SSE.
        Ожидает в body: { "version_num": <номер версии> }
        """
        letter = self.get_object()

        # ─── Гейтинг по подписке ───
        if not getattr(request.user, 'has_subscription', False):
            return Response({"locked": True},
                            status=status.HTTP_402_PAYMENT_REQUIRED)
        # ────────────────────────────

        # Берём номер версии
        version_num = request.data.get('version_num')
        if not version_num:
            return Response({"detail": "version_num is required"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Ищем версию
        try:
            version = letter.versions.get(version_num=version_num)
        except LetterVersion.DoesNotExist:
            return Response({"detail": "Version not found"},
                            status=status.HTTP_404_NOT_FOUND)

        # Загружаем текст письма из S3
        s3 = boto3.client('s3', region_name=settings.AWS_REGION)
        obj = s3.get_object(Bucket=settings.AWS_S3_BUCKET, Key=version.s3_key)
        letter_text = obj['Body'].read().decode('utf-8')

        # Собираем историю сообщений
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in version.messages.all()
        ]

        # Формируем system и user
        system_msg = {
            "role": "system",
            "content": (
                "You are a university admissions officer and academic program director. "
                "Critically evaluate the following letter using international admissions standards "
                "across six criteria: Purpose and Motivation, Academic and Professional Alignment, "
                "Depth and Specificity, Structure and Clarity, Engagement and Authenticity, Formalities."
            )
        }
        user_msg = {"role": "user", "content": letter_text}

        history.extend([system_msg, user_msg])

        # Сохраняем system+user в БД
        VersionMessage.objects.bulk_create([
            VersionMessage(version=version, role=m["role"], content=m["content"])
            for m in (system_msg, user_msg)
        ])

        # Выбираем нужного ассистента
        assistant_map = {
            'common_app': settings.ASSISTANT_COMMON_APP_ID,
            'ucas':       settings.ASSISTANT_UCAS_ID,
            'motivation': settings.ASSISTANT_MOTIVATION_ID,
        }
        assistant_id = assistant_map.get(letter.type)
        if not assistant_id:
            return Response({"detail": "Unknown letter type"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Синхронный вызов OpenAI без стрима
        try:
              # ← Старая строка openai.ChatCompletion.create() заменяется на новый интерфейс:
            completion = openai.chat.completions.create(
                #assistant = assistant_id,
                model = "gpt-4.1",
                messages = history,
                temperature = 0.7,
                #response_format = ResponseFormat.JSON_SCHEMA
            )
            content = completion.choices[0].message.content
            data = json.loads(content)

            try:
                  data = json.loads(content)
            except json.JSONDecodeError:
                return Response(
                {"detail": "Не удалось распарсить ответ OpenAI", "raw": content},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logging.exception("OpenAI analyse error")
            return Response(
                {"detail": "OpenAI error", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Сохраняем полный ответ ассистента
        VersionMessage.objects.create(
            version=version, role="assistant", content=content
        )

        # Возвращаем готовый JSON
        return Response(data, status=status.HTTP_200_OK)
