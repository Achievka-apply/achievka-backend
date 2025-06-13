from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Letter, LetterVersion
from .serializers import LetterSerializer, LetterVersionSerializer
from .s3_utils import upload_letter_text

class LetterViewSet(viewsets.ModelViewSet):
    """
    /api/letters/
    /api/letters/{pk}/
    + custom actions: /versions/
    """
    queryset = Letter.objects.all()
    serializer_class = LetterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Показываем письма только текущего пользователя
        return Letter.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get', 'post'], url_path='versions')
    def versions(self, request, pk=None):
        letter = self.get_object()

        if request.method == 'GET':
            qs = letter.versions.all()
            serializer = LetterVersionSerializer(qs, many=True)
            return Response(serializer.data)

        # POST → создать новую версию
        text     = request.data.get('text', '')
        autosave = request.data.get('autosave', True)

        # определяем следующий номер
        last = letter.versions.order_by('-version_num').first()
        next_num = (last.version_num + 1) if last else 1

        # сохраняем в S3
        s3_key = upload_letter_text(
            user_id=str(request.user.id),
            letter_id=str(letter.id),
            version_num=next_num,
            text=text
        )
        # создаём запись
        version = LetterVersion.objects.create(
            letter=letter,
            version_num=next_num,
            s3_key=s3_key
        )

        # если autosave == False → тут можно запустить analyse_stream (шаг 5)
        # но пока просто вернём данные
        data = LetterVersionSerializer(version).data
        return Response(data, status=status.HTTP_201_CREATED)
