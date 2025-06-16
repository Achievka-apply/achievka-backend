# letters/views.py

import logging
import time
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

openai.api_key = settings.OPENAI_API_KEY


class LetterViewSet(viewsets.ModelViewSet):
    queryset = Letter.objects.all()
    serializer_class = LetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='analyse')
    def analyse(self, request, pk=None):
        """
        POST /api/letters/{id}/analyse/
        Использует Assistants API: создаёт thread, добавляет user message, запускает run,
        ждёт завершения и возвращает JSON-ответ.
        Ожидает в body: { "version_num": <номер версии> }
        """
        letter = self.get_object()

        # gating по подписке
        if not getattr(request.user, 'has_subscription', False):
            return Response({"locked": True}, status=status.HTTP_402_PAYMENT_REQUIRED)

        version_num = request.data.get("version_num")
        if not version_num:
            return Response({"detail": "version_num is required"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            version = letter.versions.get(version_num=version_num)
        except LetterVersion.DoesNotExist:
            return Response({"detail": "Version not found"},
                            status=status.HTTP_404_NOT_FOUND)

        # Загрузка текста письма из S3
        s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        obj = s3.get_object(Bucket=settings.AWS_S3_BUCKET, Key=version.s3_key)
        letter_text = obj["Body"].read().decode("utf-8")

        # Собираем историю предыдущих сообщений
        prev_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in version.messages.all()
        ]

        # Создаём новый thread
        try:
            thread = openai.beta.threads.create()
        except Exception as e:
            logging.exception("Failed to create thread")
            return Response({"detail": "OpenAI thread creation failed", "error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Помещаем в thread всю историю + текущее письмо как user
        for m in prev_messages + [{"role": "user", "content": letter_text}]:
            try:
                openai.beta.threads.messages.create(
                    thread_id=thread.id,
                    role=m["role"],
                    content=m["content"]
                )
            except Exception as e:
                logging.exception("Failed to add message to thread")
                return Response({"detail": "OpenAI thread messaging failed", "error": str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Сохраняем user-сообщение в БД
        VersionMessage.objects.create(version=version, role="user", content=letter_text)

        # Выбираем нужного Assistant по типу письма
        assistant_map = {
            "common_app": settings.ASSISTANT_COMMON_APP_ID,
            "ucas":       settings.ASSISTANT_UCAS_ID,
            "motivation": settings.ASSISTANT_MOTIVATION_ID,
        }
        assistant_id = assistant_map.get(letter.type)
        if not assistant_id:
            return Response({"detail": f"Unknown letter type {letter.type}"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Запускаем run у Assistant-а
        try:
            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )
        except Exception as e:
            logging.exception("Failed to start run")
            return Response({"detail": "OpenAI run creation failed", "error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Ожидаем завершения
        while run.status in ("queued", "in_progress"):
            time.sleep(1)
            try:
                run = openai.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            except Exception as e:
                logging.exception("Failed to retrieve run status")
                return Response({"detail": "OpenAI run polling failed", "error": str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Забираем ответы из thread.messages
        try:
            msgs = openai.beta.threads.messages.list(thread_id=thread.id)
        except Exception as e:
            logging.exception("Failed to list thread messages")
            return Response({"detail": "OpenAI thread list failed", "error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Первый ответ от ассистента
        if not msgs.data:
            return Response({"detail": "No assistant response"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        assistant_reply = msgs.data[0].content[0].text.value

        # Парсим JSON из текста
        try:
            data = json.loads(assistant_reply)
        except json.JSONDecodeError:
            logging.error("Invalid JSON from assistant: %s", assistant_reply)
            return Response(
                {"detail": "Non-JSON from OpenAI", "raw": assistant_reply},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Сохраняем ответ ассистента в БД
        VersionMessage.objects.create(
            version=version, role="assistant", content=assistant_reply
        )

        return Response(data, status=status.HTTP_200_OK)
