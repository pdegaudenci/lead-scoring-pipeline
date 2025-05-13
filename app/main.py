from fastapi import FastAPI, File, UploadFile
from upload_s3 import upload_file
from snowflake_client import get_connection
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
    content = await file.read()
    
    # Subir el archivo a S3
    upload_file(file.filename, content)

    # Subir el archivo a Snowflake y ejecutar el COPY INTO
    result = upload_to_snowflake(file.filename)

    return result