from fastapi import FastAPI, File, UploadFile, Response, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from deprecated import deprecated

app = FastAPI()

# CORS configuration
origins = [
    # "http://localhost:3000",
    # "http://localhost:3001",
    # "http://localhost:8000",
    # "https://redesigned-space-fortnight-q6wqxvxwpjr24gxr.github.dev",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hello from Lambda"}

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@deprecated(reason="Usa la función `/generate-presigned-url` en su lugar.")
@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    from .upload_s3 import upload_file
    content = await file.read()
    result = upload_file(file.filename, content)
    return {"status": "File uploaded successfully", "filename": result}

@app.post("/clean-upload-and-generate-url")
async def clean_upload_and_generate_url(file: UploadFile = File(...)):
    import tempfile, os
    import pandas as pd
    import boto3
    import chardet
    import logging
    from fastapi import HTTPException
    from .upload_s3 import upload_file  # función que sube a S3 y devuelve la key

    BUCKET_NAME = "leads-raw"
    s3_client = boto3.client("s3")

    try:
        # 1. Guardar contenido temporalmente
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # 2. Detectar encoding automáticamente
        with open(tmp_file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            detected_encoding = result['encoding'] or 'latin1'
            logging.info(f"Encoding detectado: {detected_encoding}")

        # 3. Leer y limpiar CSV con pandas
        try:
            df = pd.read_csv(tmp_file_path, encoding=detected_encoding, errors="replace")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error leyendo el CSV: {str(e)}")

        df.fillna("", inplace=True)
        df.columns = [col.strip().replace(" ", "_") for col in df.columns]

        # 4. Guardar archivo limpio
        cleaned_file_path = tmp_file_path.replace(".csv", "_cleaned.csv")
        df.to_csv(cleaned_file_path, index=False)

        # 5. Subir a S3
        with open(cleaned_file_path, "rb") as cleaned_file:
            cleaned_content = cleaned_file.read()
            cleaned_filename = file.filename.replace(".csv", "_cleaned.csv")
            s3_key = upload_file(cleaned_filename, cleaned_content)

        # 6. (Opcional) Generar URL de descarga firmada
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
                ExpiresIn=3600
            )
        except Exception as e:
            logging.warning(f"No se pudo generar URL firmada: {e}")
            presigned_url = None

        return {
            "status": "Archivo limpiado y subido a S3",
            "filename": cleaned_filename,
            "s3_key": s3_key,
            "download_url": presigned_url
        }

    finally:
        # 7. Limpieza de archivos temporales
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
        if 'cleaned_file_path' in locals() and os.path.exists(cleaned_file_path):
            os.remove(cleaned_file_path)

@deprecated(reason="Usa la función `/generate-presigned-url` en su lugar.")
@app.post("/process-s3-file")
async def process_s3_file(payload: dict):
    from .snowflake_client import upload_to_snowflake_snowpipe_s3
    import logging

    s3_key = payload.get("s3_key")
    if not s3_key:
        raise HTTPException(status_code=400, detail="Missing s3_key in payload")

    logging.info(f"Processing file in S3: {s3_key}")
    result = upload_to_snowflake_snowpipe_s3(s3_key)
    return {"status": "processed", "result": result}


@app.get("/leads")
def get_leads(limit: int = 10):
    from .snowflake_client import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM LEADS_DB.INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'LEADS_FINAL'
            AND TABLE_SCHEMA = 'PUBLIC'
            ORDER BY ORDINAL_POSITION
        """)
        columns = [f'"{row[0]}"' for row in cursor.fetchall()][2:]
        columns_sql = ", ".join(columns)
        cursor.execute(f"""SELECT {columns_sql} FROM LEADS_DB.PUBLIC.LEADS_FINAL LIMIT {limit}""")
        rows = cursor.fetchall()
        clean_columns = [col.replace('"', '') for col in columns]
        return [dict(zip(clean_columns, row)) for row in rows]
    finally:
        cursor.close()
        conn.close()


@deprecated(reason="Usa la función `/generate-presigned-url` en su lugar.")
@app.post("/upload-and-load")
async def upload_and_load(file: UploadFile = File(...)):
    import tempfile, os
    import pandas as pd
    from .upload_s3 import upload_file
    from .snowflake_client import upload_to_snowflake

    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    df = pd.read_csv(tmp_file_path, encoding="latin1")
    df.fillna("", inplace=True)
    df.columns = [col.strip().replace(" ", "_") for col in df.columns]
    cleaned_file_path = tmp_file_path.replace(".csv", "_cleaned.csv")
    df.to_csv(cleaned_file_path, index=False)

    upload_file(file.filename, content)
    result = upload_to_snowflake(cleaned_file_path, file.filename)

    os.remove(tmp_file_path)
    os.remove(cleaned_file_path)

    return {"status": "File processed and loaded to Snowflake", "filename": file.filename}


@deprecated(reason="Usa la función `/generate-presigned-url` en su lugar.")
@app.post("/upload-and-load-snowpipe")
async def upload_and_load_snowpipe(file: UploadFile = File(...)):
    from .upload_s3 import upload_file
    from .snowflake_client import upload_to_snowflake_snowpipe_s3

    content = await file.read()
    s3_filename = upload_file(file.filename, content)
    result = upload_to_snowflake_snowpipe_s3(s3_filename)

    return {
        "status": "Archivo subido a S3 y Snowpipe activado",
        "filename": s3_filename,
        "snowpipe_result": result
    }

@app.get("/download")
def download_file():
    from fastapi import Response
    from .snowflake_client import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
    SELECT $1
    FROM @leads_internal_stage/tmprqsaeu0j_cleaned.json/tmprqsaeu0j_cleaned.json.gz
    (FILE_FORMAT => 'json_as_variant')
    LIMIT 100;
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    content = "\n".join([str(row[0]) for row in rows])
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=prospectos.json"}
    )

class LeadScore(BaseModel):
    id: Optional[int]
    activity_score: Optional[float]
    lead_grade: Optional[str]
    lead_stage: Optional[str]
    score: Optional[float]

@app.get("/score-all-leads", response_model=List[LeadScore])
def score_all_leads():
    from .snowflake_client import get_connection
    query = """
        SELECT 
            "Lead_Number" AS id,
            "Asymmetrique_Activity_Score" AS activity_score,
            "Lead_Grade",
            "Lead_Stage",
            SCORING_UDF("Asymmetrique_Activity_Score", "Lead_Grade", "Lead_Stage") AS score
        FROM leads_final
        LIMIT 100
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    result = []
    for row in rows:
        if len(row) != 5 or None in row:
            continue
        result.append({
            "id": row[0],
            "activity_score": row[1],
            "lead_grade": row[2],
            "lead_stage": row[3],
            "score": row[4]
        })
    return result

@app.post("/score-lead")
def score_lead(payload: dict):
    from .sagemaker_client import call_sagemaker
    result = call_sagemaker(payload)
    return result

@app.get("/lead-count")
def count_leads():
    from .athena_client import run_athena_query
    query = "SELECT COUNT(*) AS total FROM leads_raw"
    result = run_athena_query(query)
    return {"total": result}
@app.post("/test-upload-s3-file")
def test_upload_s3_file():
    """
    Simula que un archivo llamado 'demo_test.csv' ya fue subido a S3
    y lo procesa con Snowpipe.
    """
    from .snowflake_client import upload_to_snowflake_snowpipe_s3
    import logging

    test_filename = "demo_test.csv"  # cambia por un archivo real que hayas subido
    logging.info(f"[TEST] Simulating processing of S3 file: {test_filename}")

    try:
        result = upload_to_snowflake_snowpipe_s3(test_filename)
        return {
            "status": "success",
            "message": f"Archivo '{test_filename}' procesado con Snowpipe",
            "snowpipe_result": result
        }
    except Exception as e:
        logging.error(f"[TEST] Error processing test file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Lambda adapter
from mangum import Mangum
handler = Mangum(app)
