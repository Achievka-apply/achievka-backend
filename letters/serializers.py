
from rest_framework import serializers
from .models import Letter, LetterVersion, DraftLetter, DraftAnswer, DraftSection

class LetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Letter
        fields = ['id', 'name', 'type', 'program', 'created_at', 'updated_at']

class LetterVersionSerializer(serializers.ModelSerializer):
    presigned_url = serializers.SerializerMethodField()

    class Meta:
        model = LetterVersion
        fields = ['id', 'version_num', 's3_key', 'created_at', 'checked_at', 'presigned_url']

    def get_presigned_url(self, obj):
        from .s3_utils import get_presigned_url
        return get_presigned_url(obj.s3_key)


class DraftAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DraftAnswer
        fields = ['id', 'question_key', 'answer_text', 'order', 'updated_at']


class DraftSectionSerializer(serializers.ModelSerializer):
    presigned_url = serializers.SerializerMethodField()

    class Meta:
        model = DraftSection
        fields = [
            'id', 'section_key', 'prompt_hint', 'tone_style',
            'user_text', 'order', 'updated_at', 'presigned_url'
        ]

    def get_presigned_url(self, obj):
        from .s3_utils import get_presigned_url
        key = f"user_{obj.draft_letter.user.id}/draft_{obj.draft_letter.id}/section_{obj.section_key}.txt"
        return get_presigned_url(key)


class DraftLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DraftLetter
        fields = ['id', 'name', 'type', 'program', 'status', 'created_at', 'updated_at']