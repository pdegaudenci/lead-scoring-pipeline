
# Dashboard de Leads

Este proyecto es un dashboard interactivo para visualizar los leads desde Snowflake usando FastAPI.

## Instrucciones de Uso

### Instalación de Dependencias

```bash
npm install
```

### Iniciar el Servidor de Desarrollo

```bash
npm start
```

### Compilar para Producción

```bash
npm run build
```

## Dependencias Principales

- React
- Axios
- Recharts
- Tailwind CSS

# 🧠 Lead Scoring Pipeline with Snowflake

This project creates an automated pipeline for ingesting, validating, and scoring marketing leads using Snowflake, including dynamic schema inference and a scoring UDF exposed via FastAPI.

---

## 🧱 Step 1: Database and Table Setup

```sql
CREATE DATABASE IF NOT EXISTS LEADS_DB;
USE DATABASE LEADS_DB;
USE SCHEMA PUBLIC;
```

Retrieve all columns from the final structured table:

```sql
SELECT COLUMN_NAME 
FROM LEADS_DB.INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'LEADS_FINAL'
  AND TABLE_SCHEMA = 'PUBLIC'
  AND COLUMN_NAME != 'filename'
ORDER BY ORDINAL_POSITION;
```

---

## ☁️ Step 2: External Stage & File Format Setup

```sql
CREATE OR REPLACE STORAGE INTEGRATION s3_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = S3
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = '<your-AWS-role-arn>'
  STORAGE_ALLOWED_LOCATIONS = ('s3://my-leads-bucket/');
```

Create a file format and stage for ingestion:

```sql
CREATE OR REPLACE FILE FORMAT csv_as_variant
  TYPE = 'CSV'
  FIELD_DELIMITER = '\t'
  SKIP_HEADER = 1
  NULL_IF = ('', 'NULL')
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

CREATE OR REPLACE STAGE leads_internal_stage
  FILE_FORMAT = csv_as_variant;
```

---

## 📥 Step 3: Raw Table for Ingested Data

```sql
CREATE OR REPLACE TABLE leads_raw (
    filename STRING,
    data VARIANT
);
```

---

## 📦 Step 4: Snowpipe (Manual Trigger)

```sql
CREATE OR REPLACE PIPE LEADS_PIPE
AUTO_INGEST = FALSE
AS
COPY INTO leads_raw
FROM (
  SELECT METADATA$FILENAME AS filename,
         PARSE_JSON($1) AS data
  FROM @leads_internal_stage
)
FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1 FIELD_DELIMITER = '\t');
```

---

## 🔍 Step 5: JSON Format & Manual Load (for gzip files)

```sql
CREATE OR REPLACE FILE FORMAT json_as_variant
  TYPE = 'JSON'
  COMPRESSION = 'GZIP';

CREATE OR REPLACE STAGE leads_internal_stage
  FILE_FORMAT = json_as_variant;

COPY INTO leads_raw(filename, data)
FROM (
  SELECT 'file1.json.gz' AS filename, $1
  FROM @leads_internal_stage/file1.json.gz
)
FILE_FORMAT = (FORMAT_NAME = 'json_as_variant')
ON_ERROR = 'CONTINUE';
```

---

## 🧩 Step 6: Flatten & Dynamic Schema Creation

Dynamic table creation from `leads_raw.data`:

```sql
CALL create_leads_final();
```

See the full procedure in the source repo for column inference and dynamic inserts.

---

## 🧪 Step 7: Validation Procedure (Optional)

This JS stored procedure checks file structure:

```sql
CALL validate_and_load_json();
```

It infers file schema, counts rows and columns, and logs file metadata.

---

## 📊 Step 8: Lead Scoring UDF

```sql
CREATE OR REPLACE FUNCTION SCORING_UDF(
    activity_score FLOAT,
    lead_grade STRING,
    lead_stage STRING
)
RETURNS FLOAT
LANGUAGE SQL
AS
$$
    CASE
        WHEN lead_grade = 'A' THEN activity_score + 50
        WHEN lead_grade = 'B' THEN activity_score + 30
        WHEN lead_grade = 'C' THEN activity_score + 10
        ELSE activity_score
    END
    +
    CASE
        WHEN lead_stage = 'Qualified' THEN 20
        WHEN lead_stage = 'Unreachable' THEN 5
        ELSE 0
    END
$$;
```

---

## 🚀 Example Query with Scoring

```sql
SELECT 
    "Lead_Number" AS id,
    "Asymmetrique_Activity_Score" AS activity_score,
    "Lead_Grade",
    "Lead_Stage",
    SCORING_UDF("Asymmetrique_Activity_Score", "Lead_Grade", "Lead_Stage") AS score
FROM leads_final
LIMIT 100;
```
