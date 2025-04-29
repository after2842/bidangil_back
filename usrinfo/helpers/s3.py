import uuid, boto3, mimetypes
from django.conf import settings

s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name="us-west-1",
)

BUCKET = "bidangilimage"

def upload_png(file_bytes: bytes, *, folder: str, extention:str, content_type:str) -> str:
    key = f"{folder}/{uuid.uuid4()}.{extention}"
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
        #ACL="public-read",    
    )
    return 'https://bidangilimage.s3.us-west-1.amazonaws.com/'+key

