import boto3
import json
import os

# Configuración del endpoint (puedes también usar variables de entorno)
SAGEMAKER_ENDPOINT = os.getenv("SAGEMAKER_ENDPOINT", "lead-scoring-endpoint")
REGION = os.getenv("AWS_REGION", "eu-west-1")

# Cliente SageMaker
sagemaker_runtime = boto3.client("sagemaker-runtime", region_name=REGION)

def call_sagemaker(payload: dict):
    """
    Envía un payload JSON a un endpoint de SageMaker y devuelve la predicción.
    """
    try:
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT,
            ContentType="application/json",
            Body=json.dumps(payload)
        )
        result = json.loads(response["Body"].read().decode())
        return result
    except Exception as e:
        return {"error": str(e)}
