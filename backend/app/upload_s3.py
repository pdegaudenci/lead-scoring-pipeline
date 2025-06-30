import boto3
import os
import io
import logging
from typing import Any
from botocore.exceptions import ClientError, NoCredentialsError

# Configuración del cliente S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
    endpoint_url=os.environ.get("S3_ENDPOINT_URL", "http://localhost:4566"),  # "http://localstack:4566" en docker
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)

# Nombre del bucket
bucket = os.environ.get("S3_BUCKET", "leads-raw")

def ensure_bucket_exists():
    """
    Verifica si el bucket existe y lo crea si no.
    Solo necesario en LocalStack o entornos de prueba.
    """
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404' or error_code == 'NoSuchBucket':
            logging.warning(f"Bucket '{bucket}' no encontrado. Creando...")
            s3.create_bucket(Bucket=bucket)
        else:
            logging.error(f"Error al verificar bucket: {e}")
            raise

def upload_file(filename: str, content: Any) -> str:
    """
    Sube un archivo a S3 (LocalStack o AWS).
    
    Args:
        filename (str): nombre del archivo que se almacenará en S3
        content (Any): contenido binario del archivo

    Returns:
        str: nombre del archivo subido (key en S3)
    
    Raises:
        Exception: si la subida falla
    """
    if not filename or not content:
        raise ValueError("El nombre y contenido del archivo no pueden estar vacíos.")
    
    try:
        ensure_bucket_exists()
        file_obj = io.BytesIO(content)

        s3.upload_fileobj(file_obj, bucket, filename)
        logging.info(f"✅ Archivo '{filename}' subido correctamente a bucket '{bucket}'")
        return filename

    except NoCredentialsError:
        logging.error("❌ Credenciales de AWS no encontradas.")
        raise Exception("Credenciales de AWS no encontradas.")

    except ClientError as e:
        logging.error(f"❌ Error al subir archivo a S3: {e}")
        raise Exception(f"Error al subir archivo a S3: {e}")

    except Exception as e:
        logging.error(f"❌ Error inesperado: {e}")
        raise Exception(f"Error inesperado al subir a S3: {e}")
