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

from .models import Letter, LetterVersion, VersionMessage
from .serializers import LetterSerializer, LetterVersionSerializer
from .s3_utils import upload_letter_text

# Устанавливаем ключ OpenAI
openai.api_key = settings.OPENAI_API_KEY


class LetterViewSet(viewsets.ModelViewSet):
    """
    CRUD-эндпоинты для писем + версии + analyse
    с «памятью» прошлых сообщений и гейтингом по подписке.
    """
    queryset = Letter.objects.all()
    serializer_class = LetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Пользователь видит только свои письма
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # При создании письма фиксируем владельца
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get', 'post'], url_path='versions')
    def versions(self, request, pk=None):
        """
        GET  /api/letters/{id}/versions/  — список версий
        POST /api/letters/{id}/versions/ — сохранить новую версию письма в S3
        """
        letter = self.get_object()

        if request.method == 'GET':
            qs = letter.versions.all()
            serializer = LetterVersionSerializer(qs, many=True)
            return Response(serializer.data)

        # POST → новая версия
        text = request.data.get('text', '')
        autosave = request.data.get('autosave', True)

        last = letter.versions.order_by('-version_num').first()
        next_num = (last.version_num + 1) if last else 1

        s3_key = upload_letter_text(
            user_id=str(request.user.id),
            letter_id=str(letter.id),
            version_num=next_num,
            text=text
        )

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
        Ожидает в body: { "version_num": <номер версии> }
        Возвращает полный JSON-ответ от вашего Assistant на платформе OpenAI.
        """
        letter = self.get_object()

        # Гейтинг по подписке
        if not getattr(request.user, 'has_subscription', False):
            return Response(
                {"locked": True},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )

        version_num = request.data.get('version_num')
        if not version_num:
            return Response(
                {"detail": "version_num is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            version = letter.versions.get(version_num=version_num)
        except LetterVersion.DoesNotExist:
            return Response(
                {"detail": "Version not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Загрузка текста письма из S3
        s3 = boto3.client('s3', region_name=settings.AWS_REGION)
        obj = s3.get_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=version.s3_key
        )
        letter_text = obj['Body'].read().decode('utf-8')

        # Собираем всю историю (system/user/assistant) из прошлых VersionMessage
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in version.messages.all()
        ]
        # Добавляем новое пользовательское сообщение
        history.append({"role": "user", "content": letter_text})

        # Сохраняем user‐message в БД
        VersionMessage.objects.create(
            version=version, role="user", content=letter_text
        )

        # Выбираем заранее настроенного Assistant по типу письма
        assistant_map = {
            'common_app': settings.ASSISTANT_COMMON_APP_ID,
            'ucas':       settings.ASSISTANT_UCAS_ID,
            'motivation': settings.ASSISTANT_MOTIVATION_ID,
        }
        assistant_id = assistant_map.get(letter.type)
        if not assistant_id:
            return Response(
                {"detail": f"Unknown letter type {letter.type}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Синхронный вызов Assistant (все системные подсказки уже внутри него)
        try:
            completion = openai.chat.completions.create(
                assistant=assistant_id,
                messages=history,
                temperature=0.7,
            )
            content = completion.choices[0].message.content
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                logging.error("OpenAI returned non-JSON: %s", content)
                return Response(
                    {
                        "detail": "OpenAI вернул невалидный JSON",
                        "raw": content
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logging.exception("OpenAI analyse error")
            return Response(
                {"detail": "OpenAI error", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Сохраняем ответ ассистента
        VersionMessage.objects.create(
            version=version, role="assistant", content=content
        )

        # Возвращаем готовый JSON во фронт
        return Response(data, status=status.HTTP_200_OK)
