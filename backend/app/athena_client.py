import boto3
import time
import os

# Configuración
ATHENA_OUTPUT = os.getenv("ATHENA_OUTPUT", "s3://lead-scoring-athena-results/")
ATHENA_DB = os.getenv("ATHENA_DATABASE", "leads")
REGION = os.getenv("AWS_REGION", "eu-west-1")

athena = boto3.client("athena", region_name=REGION)

def run_athena_query(query: str) -> int:
    """
    Ejecuta una consulta SQL en Athena y devuelve un resultado numérico simple.
    """
    try:
        response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={"Database": ATHENA_DB},
            ResultConfiguration={"OutputLocation": ATHENA_OUTPUT}
        )
        execution_id = response["QueryExecutionId"]

        # Esperar hasta que termine la ejecución
        while True:
            status = athena.get_query_execution(QueryExecutionId=execution_id)
            state = status["QueryExecution"]["Status"]["State"]
            if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
                break
            time.sleep(1)

        if state != "SUCCEEDED":
            return -1

        # Obtener resultado
        result = athena.get_query_results(QueryExecutionId=execution_id)
        row = result["ResultSet"]["Rows"][1]  # fila 0 = encabezado
        value = int(row["Data"][0]["VarCharValue"])
        return value
    except Exception as e:
        print("Athena error:", e)
        return -1
