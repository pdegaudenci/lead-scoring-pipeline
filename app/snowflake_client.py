import os
import snowflake.connector
from pathlib import Path
from dotenv import load_dotenv
import logging
env_path = Path("env") / ".env"
load_dotenv(dotenv_path=env_path)

def get_connection():
    """
    Establece conexión a Snowflake y verifica si se ha realizado correctamente.
    """
    try:
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
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_TIMESTAMP")
        result = cursor.fetchone()  # Obtener el resultado de la consulta
        print(f"Conexión a Snowflake exitosa, Timestamp: {result[0]}")
        cursor.close()
        
        return conn  # Devolver la conexión si todo es correcto
    except Exception as e:
        print(f"Error al conectar a Snowflake: {str(e)}")
        return None  # Si hay error, devolver None
    
# Función para subir el archivo a Snowflake
def upload_to_snowflake(filepath: str, filename: str):
    """
    Sube archivo JSON a un stage y lo carga como objetos JSON en la tabla leads_raw
    """
    sf_stage = "leads_internal_stage"
    file_format = "json_as_variant"
    
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Subir archivo JSON al stage
        put_command = f"PUT file://{filepath} @{sf_stage}/{filename} AUTO_COMPRESS=TRUE OVERWRITE=TRUE"
        cursor.execute(put_command)
        logging.info(f"✅ Archivo subido al stage: {put_command}")

        # Cargar el JSON a la tabla leads_raw
        copy_command = f"""
            COPY INTO leads_raw(filename, data)
            FROM (
                SELECT '{filename}' AS filename, $1
                FROM @{sf_stage}/{filename}.gz
            )
            FILE_FORMAT = (FORMAT_NAME = '{file_format}')
            ON_ERROR = 'CONTINUE'
        """
        cursor.execute(copy_command)
        logging.info(f"🚀 Datos copiados a leads_raw: {copy_command}")

        cursor.close()
        conn.close()

        return {"status": "file uploaded and copied into Snowflake", "filename": filename}

    except Exception as e:
        logging.error(f"❌ Error al subir el archivo a Snowflake: {e}")
        return {"status": "error", "message": f"Exception occurred: {str(e)}"}

