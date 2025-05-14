from fastapi import FastAPI, File, UploadFile
from upload_s3 import upload_file
from snowflake_client import get_connection, upload_to_snowflake
import tempfile

app = FastAPI()

@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    # Leer el contenido del archivo como bytes
    content = await file.read()
    
    # Subir archivo a S3
    result = upload_file(file.filename, content)
    
    return {"status": "File uploaded successfully", "filename": result}

@app.get("/leads/")
def get_leads(limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
            SELECT 
                filename,
                data:"Prospect ID"::STRING AS prospect_id,
                data:"Lead Origin"::STRING AS origin,
                data:"Lead Score"::NUMBER AS score
            FROM leads_raw
            LIMIT {limit}
        """)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        cursor.close()
        conn.close()


# Endpoint para subir archivo a S3 y cargarlo en Snowflake
@app.post("/upload-and-load/")
async def upload_and_load(file: UploadFile = File(...)):
    # Lectura de fichero  memoria
    content = await file.read()
    
    # Guardar el archivo en disco temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    # Subir a S3 si es necesario
    upload_file(file.filename, content)

    # Llamar función de carga a Snowflake usando la ruta real del archivo
    result = upload_to_snowflake(tmp_file_path, file.filename)
    # Subir el archivo a S3
    upload_file(file.filename, content)

    # Subir el archivo a Snowflake y ejecutar el COPY INTO
    result = upload_to_snowflake(tmp_file_path, file.filename)

    return result 