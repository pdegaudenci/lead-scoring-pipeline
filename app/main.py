""" from fastapi import FastAPI, File, UploadFile
from upload_s3 import upload_file
from snowflake_client import get_connection, upload_to_snowflake
import tempfile
import os
from pyspark.sql import SparkSession

app = FastAPI()

# Configurar Spark
spark = SparkSession.builder \
    .appName("LeadScoringPipeline") \
    .master("local[*]") \
    .getOrCreate()
 
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
        cursor.execute(f
            SELECT 
                filename,
                data:"Prospect ID"::STRING AS prospect_id,
                data:"Lead Origin"::STRING AS origin,
                data:"Lead Score"::NUMBER AS score
            FROM leads_raw
            LIMIT {limit}
        )
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        cursor.close()
        conn.close()


# Endpoint para subir archivo a S3 y cargarlo en Snowflake con preprocesamiento usando PySpark
@app.post("/upload-and-load/")
async def upload_and_load(file: UploadFile = File(...)):
    # Leer el archivo CSV a DataFrame
    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    # Preprocesar archivo CSV usando PySpark
    df = spark.read.option("header", "true").option("inferSchema", "true").csv(tmp_file_path)
    df = df.fillna("")  # Reemplazar NaN con cadenas vacías
    df = df.select([col.strip().replace(" ", "_") for col in df.columns])  # Remover espacios en nombres de columnas
    
    # Guardar el DataFrame limpio para Snowflake
    cleaned_file_path = tmp_file_path.replace(".csv", "_cleaned.csv")
    df.coalesce(1).write.mode("overwrite").option("header", "true").csv(cleaned_file_path)

    # Subir a S3
    upload_file(file.filename, content)

    # Subir a Snowflake
    result = upload_to_snowflake(cleaned_file_path, file.filename)

    # Borrar el archivo temporal
    os.remove(tmp_file_path)

    return {"status": "File processed and loaded to Snowflake", "filename": file.filename}
 """
from fastapi import FastAPI, File, UploadFile, Response
from upload_s3 import upload_file
from snowflake_client import get_connection, upload_to_snowflake
import tempfile
import os
import pandas as pd
import logging
import json

import gzip


app = FastAPI()


# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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


# Endpoint para subir archivo a S3 y cargarlo en Snowflake con preprocesamiento usando PandasY

@app.post("/upload-and-load/")
async def upload_and_load(file: UploadFile = File(...)):
    # Leer el archivo CSV a DataFrame
    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    # Preprocesar archivo CSV usando Pandas
    logging.info("🔄 Iniciando preprocesamiento con Pandas...")
    df = pd.read_csv(tmp_file_path, encoding="latin1")
    original_columns = df.columns.tolist()
    logging.info(f"📊 Columnas originales: {original_columns}")

    # Reemplazar NaN con cadenas vacías y contar cambios
    df.fillna("", inplace=True)

    # Remover espacios en nombres de columnas
    df.columns = [col.strip().replace(" ", "_") for col in df.columns]

    # Convertir filas a JSON para Snowflake
    json_records = df.to_dict(orient="records")
    #cleaned_file_path = tmp_file_path.replace(".csv", ".json")
    cleaned_file_path = tmp_file_path.replace(".csv", "_cleaned.json")

    with open(cleaned_file_path, "w", encoding="utf-8") as json_file:
        for record in json_records:
            json_file.write(json.dumps(record, ensure_ascii=False) + "\n")
        logging.info(f"💾 Archivo JSON limpio guardado en: {cleaned_file_path}")

    # Subir a Snowflake
    result = upload_to_snowflake(cleaned_file_path, cleaned_file_path.split('/')[-1])
 
    # Borrar el archivo temporal
    os.remove(tmp_file_path)

    logging.info(f"🚀 Archivo {file.filename} procesado y cargado a Snowflake")

    return {"status": "File processed and loaded to Snowflake", "filename": file.filename}
    # Leer el archivo CSV a DataFrame


@app.get("/download")
def download_file():
    # Conectar a Snowflake
    conn = get_connection()

    cursor = conn.cursor()

    # Descargar contenido del archivo desde la internal stage
    sql = """
    SELECT $1
    FROM @leads_internal_stage/tmprqsaeu0j_cleaned.json/tmprqsaeu0j_cleaned.json.gz
    (FILE_FORMAT => 'json_as_variant')
    LIMIT 100;
    """
    cursor.execute(sql)
    rows = cursor.fetchall()

    # Construir contenido como string JSONL (una línea por registro)
    content = "\n".join([str(row[0]) for row in rows])

    # Retornar como archivo descargable
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=prospectos.json"}
    )
