import os
import snowflake.connector
from pathlib import Path
from dotenv import load_dotenv

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
    Sube archivo CSV a un stage y lo carga como objetos JSON en la tabla leads_raw
    """
    sf_stage = "leads_internal_stage"
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Subir archivo al stage
        cursor.execute(f"PUT file://{filepath} @{sf_stage}/{filename} OVERWRITE = TRUE")

        # Cargar archivo CSV como una fila por registro y convertir a OBJECT (VARIANT)
        cursor.execute(f"""
            COPY INTO leads_raw
            FROM (
                SELECT
                    PARSE_JSON(OBJECT_CONSTRUCT(*))
                FROM @{sf_stage}/{filename}
                FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1)
            )
            FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1)
            ON_ERROR = 'CONTINUE'
            ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
        """)

        cursor.close()
        conn.close()

        return {"status": "file uploaded and copied into Snowflake", "filename": filename}
    except Exception as e:
        return {"status": "error", "message": f"Exception occurred: {str(e)}"}
