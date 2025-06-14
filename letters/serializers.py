
from rest_framework import serializers
from .models import Letter, LetterVersion

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