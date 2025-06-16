# letters/views.py

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

    @action(detail=True, methods=['get', 'post'], url_path='versions')
    def versions(self, request, pk=None):
        # (оставляем без изменений)
        ...

    @action(detail=True, methods=['post'], url_path='analyse')
    def analyse(self, request, pk=None):
        """
        POST /api/letters/{id}/analyse/
        Сохраняет новую версию в S3 и возвращает финальный JSON-ответ от OpenAI.
        Ожидает в body: { "version_num": <номер версии> }
        """
        letter = self.get_object()

        # gating по подписке
        if not getattr(request.user, 'has_subscription', False):
            return Response({"locked": True}, status=status.HTTP_402_PAYMENT_REQUIRED)

        ver_num = request.data.get('version_num')
        if not ver_num:
            return Response(
                {"detail": "version_num is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            version = letter.versions.get(version_num=ver_num)
        except LetterVersion.DoesNotExist:
            return Response({"detail": "Version not found"}, status=status.HTTP_404_NOT_FOUND)

        # загрузка текста из S3
        s3 = boto3.client('s3', region_name=settings.AWS_REGION)
        obj = s3.get_object(Bucket=settings.AWS_S3_BUCKET, Key=version.s3_key)
        letter_text = obj["Body"].read().decode("utf-8")

        # собираем историю
        history = []
        for msg in version.messages.all():
            history.append({"role": msg.role, "content": msg.content})

        system_msg = {
            "role": "system",
            "content": (
                "You are a university admissions officer and academic program director. "
                "Critically evaluate the following letter using six criteria: "
                "Purpose and Motivation, Academic Alignment, Depth and Specificity, "
                "Structure and Clarity, Engagement and Authenticity, Formalities."
            )
        }
        user_msg = {"role": "user", "content": letter_text}
        history.extend([system_msg, user_msg])

        # сохраняем system+user в БД
        VersionMessage.objects.bulk_create([
            VersionMessage(version=version, role=m["role"], content=m["content"])
            for m in (system_msg, user_msg)
        ])

        # выбор ассистента
        assistant_map = {
            "common_app": settings.ASSISTANT_COMMON_APP_ID,
            "ucas":       settings.ASSISTANT_UCAS_ID,
            "motivation": settings.ASSISTANT_MOTIVATION_ID,
        }
        assistant_id = assistant_map.get(letter.type)
        if not assistant_id:
            return Response({"detail": "Unknown letter type"}, status=status.HTTP_400_BAD_REQUEST)

        # **СИНХРОННЫЙ ВЫЗОВ** OpenAI без stream
        try:
            completion = openai.ChatCompletion.create(
                assistant=assistant_id,
                messages=history,
                temperature=0.7,
                stream=False,
                response_format="json_schema"
            )
            content = completion.choices[0].message.content
            data = json.loads(content)
        except Exception as e:
            # можете логировать
            return Response(
                {"detail": "OpenAI error", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # сохраняем полный ответ
        VersionMessage.objects.create(
            version=version, role="assistant", content=content
        )
        # возвращаем парсенный JSON
        return Response(data, status=status.HTTP_200_OK)
