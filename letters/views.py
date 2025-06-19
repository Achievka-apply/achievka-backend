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

from .models import Letter, LetterVersion, VersionMessage, DraftLetter, DraftAnswer, DraftSection
from .serializers import LetterSerializer, LetterVersionSerializer,DraftLetterSerializer, DraftAnswerSerializer, DraftSectionSerializer
from .s3_utils import upload_letter_text,  upload_draft_section
# Устанавливаем API-ключ
openai.api_key = settings.OPENAI_API_KEY


class LetterViewSet(viewsets.ModelViewSet):
    """
    CRUD-эндпоинты для писем + versions + analyse
    с учётом истории и гейтинга по подписке.
    """
    queryset = Letter.objects.all()
    serializer_class = LetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Доступ только к своим письмам
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # При создании фиксируем владельца
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get', 'post'], url_path='versions')
    def versions(self, request, pk=None):
        """
        GET  /api/letters/{id}/versions/  — список всех версий письма
        POST /api/letters/{id}/versions/  — сохранить новую версию в S3
        """
        letter = self.get_object()

        # Список версий
        if request.method == 'GET':
            qs = letter.versions.order_by('version_num')
            serializer = LetterVersionSerializer(qs, many=True)
            return Response(serializer.data)

        # Создание новой версии
        text = request.data.get('text', '')
        autosave = request.data.get('autosave', True)

        # определяем номер
        last = letter.versions.order_by('-version_num').first()
        next_num = (last.version_num + 1) if last else 1

        # заливаем текст в S3
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
        Использует Assistants API:
          1) создаёт новый thread
          2) добавляет в него всю историю + текущее письмо
          3) запускает run у вашего assistant_id
          4) ждёт завершения и возвращает JSON-ответ
        Ожидает в тело: { "version_num": <номер версии> }
        """
        letter = self.get_object()

        # gating по подписке
        if not getattr(request.user, 'has_subscription', False):
            return Response({"locked": True},
                            status=status.HTTP_402_PAYMENT_REQUIRED)

        data = request.data
        version_num = data.get("version_num")
        s3 = boto3.client("s3", region_name=settings.AWS_REGION)

        # если version_num не передан — формируем текст из входных полей
        if not version_num:
            if letter.type == "motivation":
                program    = data.get("program")
                university = data.get("university")
                if not program or not university:
                    return Response({"detail": "program и university обязательны"},
                                    status=status.HTTP_400_BAD_REQUEST)
                letter_text = f"Program: {program}\nUniversity: {university}"

            elif letter.type == "common_app":
                prompt = data.get("essay_prompt")
                if not prompt:
                    return Response({"detail": "essay_prompt обязателен"},
                                    status=status.HTTP_400_BAD_REQUEST)
                letter_text = prompt

            elif letter.type == "ucas":
                program = data.get("program")
                if not program:
                    return Response({"detail": "program обязателен"},
                                    status=status.HTTP_400_BAD_REQUEST)
                letter_text = program

            else:
                return Response({"detail": f"Unknown letter type {letter.type}"},
                                status=status.HTTP_400_BAD_REQUEST)

            # создаём новую версию в S3 и БД
            last = letter.versions.order_by("-version_num").first()
            next_num = (last.version_num + 1) if last else 1
            s3_key = upload_letter_text(
                user_id=str(request.user.id),
                letter_id=str(letter.id),
                version_num=next_num,
                text=letter_text
            )
            version = LetterVersion.objects.create(
                letter=letter,
                version_num=next_num,
                s3_key=s3_key
            )

        else:
            # старая логика: получаем существующую версию и читаем её из S3
            try:
                version = letter.versions.get(version_num=version_num)
            except LetterVersion.DoesNotExist:
                return Response({"detail": "Version not found"},
                                status=status.HTTP_404_NOT_FOUND)
            obj = s3.get_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=version.s3_key
            )
            letter_text = obj["Body"].read().decode("utf-8")

        # история прошлых сообщений
        prev_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in version.messages.all()
        ]

        # создаём новый thread
        try:
            thread = openai.beta.threads.create()
        except Exception as e:
            logging.exception("Failed to create thread")
            return Response(
                {"detail": "OpenAI thread creation failed", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # добавляем все сообщения в thread
        for m in prev_messages + [{"role": "user", "content": letter_text}]:
            try:
                openai.beta.threads.messages.create(
                    thread_id=thread.id,
                    role=m["role"],
                    content=m["content"]
                )
            except Exception as e:
                logging.exception("Failed to add message to thread")
                return Response(
                    {"detail": "Thread messaging failed", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # сохраняем user-сообщение в БД
        VersionMessage.objects.create(
            version=version, role="user", content=letter_text
        )

        # выбираем assistant_id по типу письма
        assistant_map = {
            "common_app": settings.ASSISTANT_COMMON_APP_ID,
            "ucas":       settings.ASSISTANT_UCAS_ID,
            "motivation": settings.ASSISTANT_MOTIVATION_ID,
        }
        assistant_id = assistant_map.get(letter.type)
        logging.info(f"Using assistant_id: {assistant_id} for letter type: {letter.type}")

        if not assistant_id:
            return Response({"detail": f"Unknown letter type {letter.type}"},
                            status=status.HTTP_400_BAD_REQUEST)

        # запускаем run
        try:
            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )
        except Exception as e:
            logging.exception("Failed to start run")
            return Response(
                {"detail": "Run creation failed", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # polling до статуса READY
        while run.status in ("queued", "in_progress"):
            time.sleep(1)
            try:
                run = openai.beta.threads.runs.retrieve(
                    thread_id=thread.id, run_id=run.id
                )
            except Exception as e:
                logging.exception("Failed to poll run status")
                return Response(
                    {"detail": "Run polling failed", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # получаем список сообщений thread’а
        try:
            msgs = openai.beta.threads.messages.list(thread_id=thread.id)
        except Exception as e:
            logging.exception("Failed to list thread messages")
            return Response(
                {"detail": "Listing thread messages failed", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if not msgs.data:
            return Response(
                {"detail": "No assistant response"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # извлекаем текст первого сообщения ассистента
        assistant_reply = msgs.data[0].content[0].text.value

        # парсим JSON
        try:
            data = json.loads(assistant_reply)
        except json.JSONDecodeError:
            logging.error("Invalid JSON from assistant: %s", assistant_reply)
            return Response(
                {"detail": "Non-JSON from OpenAI", "raw": assistant_reply},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # сохраняем ответ ассистента
        VersionMessage.objects.create(
            version=version, role="assistant", content=assistant_reply
        )

        # возвращаем распарсенный JSON
        return Response(data, status=status.HTTP_200_OK)





class DraftLetterViewSet(viewsets.ModelViewSet):
    queryset = DraftLetter.objects.all()
    serializer_class = DraftLetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'], url_path='answers')
    def list_answers(self, request, pk=None):
        draft = self.get_object()
        serializer = DraftAnswerSerializer(draft.answers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='answers')
    def save_answer(self, request, pk=None):
        draft = self.get_object()
        data = request.data
        answer, _ = DraftAnswer.objects.update_or_create(
            draft_letter=draft,
            question_key=data['question_key'],
            defaults={
                'answer_text': data.get('answer_text', ''),
                'order': data.get('order', 0)
            }
        )
        return Response(DraftAnswerSerializer(answer).data,
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='generate_structure')
    def generate_structure(self, request, pk=None):
        draft = self.get_object()

        # gating
        if not getattr(request.user, 'has_subscription', False):
            draft.status = 'locked'
            draft.save()
            return Response({"locked": True}, status=status.HTTP_402_PAYMENT_REQUIRED)

        # собираем вопросы и ответы
        qa = [
            {"key": a.question_key, "answer": a.answer_text}
            for a in draft.answers.order_by('order')
        ]

        # выбираем assistant_id
        assistant_map = {
            "common_app_create": settings.ASSISTANT_COMMON_APP_CREATE_ID,
            "ucas_create":       settings.ASSISTANT_UCAS_CREATE_ID,
            "motivation_create": settings.ASSISTANT_MOTIVATION_CREATE_ID,
        }
        assistant_id = assistant_map.get(draft.type)
        if not assistant_id:
            return Response({"detail": "Unknown draft type"}, status=400)

        # создаём thread и заливаем сообщения
        thread = openai.beta.threads.create()
        for qa_item in qa:
            openai.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=json.dumps(qa_item)
            )

        # запускаем run
        run = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
        while run.status in ("queued", "in_progress"):
            time.sleep(1)
            run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        msgs = openai.beta.threads.messages.list(thread_id=thread.id)
        if not msgs.data:
            return Response({"detail": "No assistant response"}, status=500)

        reply = msgs.data[0].content[0].text.value
        try:
            payload = json.loads(reply)
        except json.JSONDecodeError:
            return Response({"detail": "Invalid JSON", "raw": reply}, status=500)

        # очищаем старые секции и сохраняем новые
        draft.sections.all().delete()
        for idx, sec in enumerate(payload.get('sections', []), start=1):
            DraftSection.objects.create(
                draft_letter=draft,
                section_key=sec['key'],
                prompt_hint=sec['prompt_hint'],
                tone_style=sec['tone_style'],
                order=idx
            )
        draft.status = 'generated'
        draft.save()

        serializer = DraftSectionSerializer(draft.sections, many=True)
        return Response(serializer.data, status=200)

    @action(detail=True, methods=['patch'], url_path='sections/(?P<section_id>[^/.]+)')
    def update_section_text(self, request, pk=None, section_id=None):
        draft = self.get_object()
        section = draft.sections.get(id=section_id)
        section.user_text = request.data.get('user_text', '')
        section.save()
        # также сохраняем в S3
        upload_draft_section(
            user_id=str(request.user.id),
            draft_id=str(draft.id),
            section_key=section.section_key,
            text=section.user_text
        )
        return Response(DraftSectionSerializer(section).data)