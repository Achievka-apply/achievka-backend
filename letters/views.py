# letters/views.py

import boto3
import openai
from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Letter, LetterVersion, VersionMessage
from .serializers import LetterSerializer, LetterVersionSerializer
from .s3_utils import upload_letter_text, get_presigned_url

# Устанавливаем ключ OpenAI
openai.api_key = settings.OPENAI_API_KEY

class LetterViewSet(viewsets.ModelViewSet):
    """
    CRUD-эндпоинты для писем + версии + analyse_stream с памятью и динамическим выбором ассистента.
    """
    queryset = Letter.objects.all()
    serializer_class = LetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Только свои письма
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get', 'post'], url_path='versions')
    def versions(self, request, pk=None):
        """
        GET  /api/letters/{id}/versions/  — список версий
        POST /api/letters/{id}/versions/  — сохраняет новую версию письма в S3
        """
        letter = self.get_object()

        if request.method == 'GET':
            qs = letter.versions.all()
            serializer = LetterVersionSerializer(qs, many=True)
            return Response(serializer.data)

        # POST → create new version
        text     = request.data.get('text', '')
        autosave = request.data.get('autosave', True)

        # следующий version_num
        last = letter.versions.order_by('-version_num').first()
        next_num = last.version_num + 1 if last else 1

        # сохранить в S3
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

        data = LetterVersionSerializer(version).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='analyse_stream')
    def analyse_stream(self, request, pk=None):
        """
        POST /api/letters/{id}/analyse_stream/
        Запускает стриминг анализа письма, при этом модель «помнит» всю историю.
        Ожидает в теле: { "version_num": <номер версии> }
        """
        letter = self.get_object()
        version_num = request.data.get('version_num')
        if not version_num:
            return Response({"detail": "version_num is required"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Найти нужную версию
        try:
            version = letter.versions.get(version_num=version_num)
        except LetterVersion.DoesNotExist:
            return Response({"detail": "Version not found"},
                            status=status.HTTP_404_NOT_FOUND)

        # Загрузить текст письма из S3
        s3 = boto3.client('s3', region_name=settings.AWS_REGION)
        obj = s3.get_object(Bucket=settings.AWS_S3_BUCKET, Key=version.s3_key)
        letter_text = obj['Body'].read().decode('utf-8')

        # Собрать всю историю сообщений (system/user/assistant) из прошлых запусков
        history = []
        for msg in version.messages.all():  # VersionMessage instances
            history.append({"role": msg.role, "content": msg.content})

        # Системное сообщение (инструкции) и пользовательское сообщение (текст письма)
        system_msg = {
            "role": "system",
            "content": (
                "ROLE\n"
                "You are a university admissions officer and academic program director. "
                "Critically evaluate the following motivation letter using international admissions standards "
                "across six criteria: Purpose and Motivation, Academic and Professional Alignment, "
                "Depth and Specificity, Structure and Clarity, Engagement and Authenticity, Formalities and Compliance."
            )
        }
        user_msg = {"role": "user", "content": letter_text}

        # Добавляем их в историю
        history.extend([system_msg, user_msg])

        # Сохраняем новые system + user
        VersionMessage.objects.bulk_create([
            VersionMessage(version=version, role=m["role"], content=m["content"])
            for m in (system_msg, user_msg)
        ])

        # Выбираем ассистента по типу письма
        assistant_map = {
            'common_app': settings.ASSISTANT_COMMON_APP_ID,
            'ucas':       settings.ASSISTANT_UCAS_ID,
            'motivation': settings.ASSISTANT_MOTIVATION_ID,
        }
        assistant_id = assistant_map.get(letter.type)
        if not assistant_id:
            return Response({"detail": "Unknown letter type"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Стримим ответ от OpenAI через SSE
        def event_stream():
            full_reply = ""
            response = openai.ChatCompletion.create(
                assistant=assistant_id,
                messages=history,
                temperature=0.7,
                stream=True,
                response_format="json_schema"
            )
            for chunk in response:
                delta = chunk.choices[0].delta.get("content")
                if delta:
                    full_reply += delta
                    yield f"data: {delta}\n\n"
            # Сохраняем полный ответ ассистента
            VersionMessage.objects.create(
                version=version, role="assistant", content=full_reply
            )
            yield "data: [DONE]\n\n"

        return StreamingHttpResponse(event_stream(), content_type="text/event-stream")
