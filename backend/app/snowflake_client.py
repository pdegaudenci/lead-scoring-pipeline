import os
import snowflake.connector
from pathlib import Path
from dotenv import load_dotenv
import logging
import jwt
import time

import requests
from snowflake.connector import connect


# Cargar .env solo si no estás en AWS Lambda (Entorno local)
if not os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    #env_path = Path("env") / ".env"
    # Ruta relativa desde el archivo main.py a la carpeta env
    env_path = Path(__file__).resolve().parent.parent / "env" / ".env"
    load_dotenv(dotenv_path=env_path)

# Autenticacion por jwt con RSA
def generate_snowflake_jwt():
    """
    Genera un token JWT para autenticar con Snowflake REST API usando claves del .env
    """
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    private_key_path = os.getenv("PRIVATE_KEY_PATH")

    if not all([account, user, private_key_path]):
        raise Exception("Faltan variables requeridas en el archivo .env")

    with open(private_key_path, "r") as f:
        private_key = f.read()

    now = int(time.time())
    payload = {
        "iss": f"{account}.{user}",
        "sub": f"{account}.{user}",
        "iat": now,
        "exp": now + 60
    }

    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")
    return encoded_jwt
# Autenticacion usuario y password
def get_connection():
    """
    Establece conexión a Snowflake y verifica si se ha realizado correctamente.
    """
    try:
        print("ruta de env: ", env_path) 
        # Crear la conexión
        conn = snowflake.connector.connect(
            user=os.environ.get("SNOWFLAKE_USER"),
            password=os.environ.get("SNOWFLAKE_PASSWORD"),
            account=os.environ.get("SNOWFLAKE_ACCOUNT"),
            warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE"),
            database=os.environ.get("SNOWFLAKE_DATABASE"),
            schema=os.environ.get("SNOWFLAKE_SCHEMA"),
            role=os.environ.get("SNOWFLAKE_ROLE"),
        )


        # Intentar realizar una consulta simple para verificar la conexión
        cursor = conn.cursor() # esto es el numero de identificacion de la uuid  de la carga de dtaos de snowflake en la tabla final de leads 
        cursor.execute("SELECT CURRENT_TIMESTAMP")
        result = cursor.fetchone()  # Obtener el resultado de la consulta
        print(f"Conexión a Snowflake exitosa, Timestamp: {result[0]}")
        cursor.close()
        
        return conn  # Devolver la conexión si todo es correcto
    except Exception as e:
        print(f"Error al conectar a Snowflake: {str(e)}")
        return None  # Si hay error, devolver None
    
# Función para subir el archivo a internl stage Snowflake y ejecutar COPY INTO a tabla intermedia
def upload_to_snowflake(filepath: str, filename: str):
    """
    Sube archivo JSON a un stage y lo carga como objetos JSON en la tabla leads_raw
    """
    import logging
    sf_stage = "leads_internal_stage"
    file_format = "json_as_variant"

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Subir el archivo directamente a la raíz del stage (sin subcarpeta)
        put_command = f"PUT file://{filepath} @{sf_stage} AUTO_COMPRESS=TRUE OVERWRITE=TRUE"
        cursor.execute(put_command)
        logging.info(f"✅ Archivo subido al stage: {put_command}")

        # Obtener el nombre real del archivo renombrado (con UUID si aplica)
        put_result = cursor.fetchall()
        if not put_result:
            raise Exception("No se obtuvo resultado del comando PUT.")

        stage_path = put_result[0][1]  # Esto devuelve algo como @leads_internal_stage/SampleData~UUID.json.gz
        actual_filename = stage_path.split('/')[-1]


        if not actual_filename.endswith(".gz") and ".gz_" not in actual_filename:
            raise Exception(f"El archivo renombrado {actual_filename} no tiene el formato esperado .gz_UUID.")

        # Ejecutar COPY INTO usando el nombre real
        copy_command = f"""
            COPY INTO leads_raw(filename, data)
            FROM (
                SELECT '{actual_filename}' AS filename, $1
                FROM @{sf_stage}/{actual_filename}
            )
            FILE_FORMAT = (FORMAT_NAME = '{file_format}') 
            ON_ERROR = 'CONTINUE'
        """
        logging.info(f"🚀 Ejecutando comando COPY INTO: {copy_command}")
        cursor.execute(copy_command)
        logging.info("🚀 Datos copiados a leads_raw con éxito.")

        cursor.close()
        conn.close()

        return {"status": "file uploaded and copied into Snowflake", "filename": actual_filename}

    except Exception as e:
        logging.error(f"❌ Error al subir el archivo a Snowflake: {e}")
        return {"status": "error", "message": f"Exception occurred: {str(e)}"}


def upload_to_snowflake_snowpipe(filepath: str):
    sf_stage = os.getenv("SNOWFLAKE_STAGE", "leads_internal_stage")
    pipe_name = os.getenv("SNOWPIPE_NAME")
    snowflake_account = os.getenv("SNOWFLAKE_ACCOUNT")
    snowflake_user = os.getenv("SNOWFLAKE_USER")
    private_key_path = os.getenv("PRIVATE_KEY_PATH")

    # Diagnóstico
    print("🧪 Variables:")
    print(f"STAGE: {sf_stage}")
    print(f"PIPE: {pipe_name}")
    print(f"ACCOUNT: {snowflake_account}")
    print(f"USER: {snowflake_user}")
    print(f"KEY PATH: {private_key_path}")

    if not all([snowflake_account, snowflake_user, pipe_name, private_key_path]):
        raise Exception("❌ Faltan variables de entorno necesarias.")

    snowflake_host = f"https://{snowflake_account}.snowflakecomputing.com"

    try:
        conn = connect(
            user=snowflake_user,
            account=snowflake_account,
            private_key_file=private_key_path
        )
        cursor = conn.cursor()

        # Subir archivo al stage
        put_command = f"PUT file://{filepath} @{sf_stage} AUTO_COMPRESS=TRUE OVERWRITE=TRUE"
        print("🧾 Comando PUT:", put_command)
        print("📁 Filepath:", filepath)
        if not os.path.exists(filepath):
            raise Exception(f"❌ Archivo no encontrado en: {filepath}")

        cursor.execute(put_command)
        put_result = cursor.fetchall()
        cursor.close()
        conn.close()

        # Obtener el nombre real del archivo cargado (con UUID)
        full_stage_path = put_result[0][2]
        compressed_filename = os.path.basename(full_stage_path)
        print("✅ Nombre del archivo cargado:", compressed_filename)

        # Generar JWT
        token = generate_snowflake_jwt()

        # Llamar a Snowpipe REST API
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        body = {"files": [{"path": compressed_filename}]}
        url = f"{snowflake_host}/v1/data/pipes/{pipe_name}/insertFiles"

        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        logging.error(f"❌ Snowpipe error: {e}")
        return {"status": "error", "message": str(e)}


