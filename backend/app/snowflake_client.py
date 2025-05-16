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
        cursor = conn.cursor() # esto es el numero de identificacion de la uuid  de la carga de dtaos de snowflake en la tabla final de leads 
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

        # La segunda columna contiene el path completo en el stage
        stage_path = put_result[0][1]  # Ej: '@leads_internal_stage/filename.json.gz_abc123'
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
