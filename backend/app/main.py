from fastapi import FastAPI, File, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import os
import pandas as pd
import logging
import json
from mangum import Mangum

from upload_s3 import upload_file
from snowflake_client import get_connection, upload_to_snowflake, upload_to_snowflake_snowpipe, upload_to_snowflake_snowpipe_s3
from sagemaker_client import call_sagemaker
from athena_client import run_athena_query

app = FastAPI()

# Configurar CORS
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://redesigned-space-fortnight-q6wqxvxwpjr24gxr.github.dev",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    content = await file.read()
    result = upload_file(file.filename, content)
    return {"status": "File uploaded successfully", "filename": result}

@app.get("/leads/")
def get_leads(limit: int = 10):
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
        cursor.execute(f"""
            SELECT {columns_sql}
            FROM LEADS_DB.PUBLIC.LEADS_FINAL
            LIMIT {limit}
        """)
        rows = cursor.fetchall()
        clean_columns = [col.replace('"', '') for col in columns]
        return [dict(zip(clean_columns, row)) for row in rows]
    finally:
        cursor.close()
        conn.close()

@app.post("/upload-and-load/")
async def upload_and_load(file: UploadFile = File(...)):
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

@app.post("/upload-and-load-snowpipe/")
async def upload_and_load_snowpipe(file: UploadFile = File(...)):
    content = await file.read()

    # Subir archivo directamente a S3
    s3_filename = upload_file(file.filename, content)

    # Activar Snowpipe usando el archivo ya en S3
    result = upload_to_snowflake_snowpipe_s3(s3_filename)

    return {
        "status": "Archivo subido a S3 y Snowpipe activado",
        "filename": s3_filename,
        "snowpipe_result": result
    }

@app.get("/download")
def download_file():
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

@app.post("/score-lead/")
def score_lead(payload: dict):
    result = call_sagemaker(payload)
    return result

@app.get("/lead-count")
def count_leads():
    query = "SELECT COUNT(*) AS total FROM leads_raw"
    result = run_athena_query(query)
    return {"total": result}

# Adaptador Lambda
handler = Mangum(app)
