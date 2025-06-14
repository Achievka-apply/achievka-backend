
import boto3
from django.conf import settings

def upload_letter_text(user_id: str, letter_id: str, version_num: int, text: str) -> str:
    key = f"user_{user_id}/letter_{letter_id}/version_{version_num}.txt"
    s3 = boto3.client('s3', region_name=settings.AWS_REGION)
    s3.put_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=key,
        Body=text.encode('utf-8'),
        ContentType='text/plain'
    )
    return key


def get_presigned_url(key: str, expires_in: int = 900) -> str:
    s3 = boto3.client('s3', region_name=settings.AWS_REGION)
    return s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': settings.AWS_S3_BUCKET, 'Key': key},
        ExpiresIn=expires_in
    )