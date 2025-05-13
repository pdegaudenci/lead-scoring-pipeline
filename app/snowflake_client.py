import os
import snowflake.connector

def get_connection():
    """
    Establece conexión a Snowflake.
    """
    conn = snowflake.connector.connect(
        user=os.environ.get("SNOWFLAKE_USER"),
        password=os.environ.get("SNOWFLAKE_PASSWORD"),
        account=os.environ.get("SNOWFLAKE_ACCOUNT"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE"),
        database=os.environ.get("SNOWFLAKE_DATABASE"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA"),
        role=os.environ.get("SNOWFLAKE_ROLE"),
    )
    return conn
# Función para subir el archivo a Snowflake
def upload_to_snowflake(filename: str):
    """
    Realiza el PUT del archivo en el Stage de Snowflake y luego hace el COPY INTO
    """
    try:
        # Conectar a Snowflake
        conn = snowflake_connection()
        cursor = conn.cursor()

        # PUT archivo desde el directorio local
        cursor.execute(f"PUT file://{filename} @{sf_stage}/{filename} OVERWRITE = TRUE")

        # Ejecutar COPY INTO para cargar el archivo
        cursor.execute(f"""
            COPY INTO your_table
            FROM @{sf_stage}/{filename}
            FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1)
        """)

        cursor.close()
        conn.close()
        
        return {"status": "file uploaded and copied into Snowflake", "filename": filename}
    except Exception as e:
        return {"status": "error", "message": str(e)}
