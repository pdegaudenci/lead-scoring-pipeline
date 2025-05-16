import boto3
import os
from typing import Any
import io

# Cliente S3 apuntando a LocalStack
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
    endpoint_url=os.environ.get("S3_ENDPOINT_URL", "http://localstack:4566"),
    region_name="us-east-1"
)

# Bucket de destino
bucket = os.environ.get("S3_BUCKET", "leads-bucket")

def upload_file(filename: str, content: Any):
    """
    Sube un archivo a S3 (simulado con LocalStack)
    """
    try:
        ensure_bucket_exists()
        # Convertimos los bytes a un archivo en memoria
        file_obj = io.BytesIO(content)

        # Subimos el archivo
        s3.upload_fileobj(file_obj, bucket, filename)
        
        return filename
    except Exception as e:
        return str(e)

def ensure_bucket_exists():
    try:
        s3.head_bucket(Bucket=bucket)
    except:
        s3.create_bucket(Bucket=bucket)


