# Lead Scoring Pipeline

## 📋 Objetivo del Proyecto

Crear una solución que reciba datos de leads, realice una puntuación (**scoring**) utilizando un modelo simple y almacene los resultados de manera estructurada en Snowflake. Esto incluye la ingesta de datos desde S3 (simulado con AWS LocalStack), el procesamiento del scoring y la automatización de la carga de datos.

---
# 📈 Iterative Development – Sprints Overview (📅 Agile Sprint Plan). 2 Dias


## Sprint 1 - Procesamiento de Leads

### Funcionalidades Implementadas

1. **Carga de Archivos CSV y JSON**
   - Procesamiento de archivos CSV para convertirlos a formato JSON.
   - Manejo de valores nulos y limpieza de datos para asegurar la integridad.
   - Generación de archivos JSON y carga a Snowflake mediante stages internos.

2. **Optimización del Pipeline**
   - Ajustes en el formato de archivos para evitar problemas de formato (.json.gz).
   - Implementación de scripts para manejar errores de datos y compatibilidad.

3. **Validación de Archivos en Snowflake**
   - Procedimientos almacenados para validar la estructura de archivos antes de cargar.
   - Scripts para verificar la existencia de columnas y filas antes de insertar datos.
   - Pruebas en IU de Snowflake.

### Consideraciones Técnicas para la Carga y Procesamiento de Datos

1. **Separación de Tablas**
   - Se propone crear una arquitectura en dos niveles:
     - `leads_raw`: tabla intermedia que almacena los datos en formato JSON crudo.
     - `leads_final`: tabla destino con los datos desplegados en columnas estructuradas.
   - Esta separación facilita la validación, trazabilidad y transformación de los datos.

2. **Carga Incremental**
   - Para evitar duplicados y optimizar el rendimiento, se plantea implementar una estrategia de carga incremental.
   - Posibles enfoques:
     - Comparación por identificadores únicos como `Prospect_ID`.
     - Uso de campos de fecha de actualización o generación de hash/checksum de los registros.

3. **Automatización del Flujo**
   - Se evaluarán diferentes mecanismos de automatización para manejar la carga de datos de forma eficiente:
     - **Procedimientos Almacenados (PA):** encapsulan la lógica de validación y carga.
     - **TASKs:** permiten programar ejecuciones periódicas o encadenadas de PA.
     - **STREAMs:** detectan nuevos registros en `leads_raw` para alimentar `leads_final`.
     - **Snowpipe:** automatiza la ingesta continua de archivos al detectar nuevos uploads en el stage.

> Estas consideraciones permitirán escalar el pipeline de forma robusta, controlada y optimizada para entornos de producción.

   
### Problemas Encontrados

- **Errores de Compresión y Formato al subir fichero a snowflake**
  - Los archivos se estaban subiendo como `.json.gz` en lugar de `.json`, causando errores de compatibilidad.
  - Se corrigieron las configuraciones para usar formatos correctos y evitar errores de conteo de filas y columnas.
  - Snowflake renombraba automáticamente los archivos con un UUID cuando se usaba `AUTO_COMPRESS=TRUE`, lo que causaba errores al referenciar el archivo en el comando `COPY INTO` (Por lo tanto, el fichero se cargaba en la internal stage pero no se cargaba en la tabla destino.)

- **Errores en Procedimientos Almacenados**
  - Varios errores de sintaxis en procedimientos almacenados de Snowflake que requerían ajustes en la lógica.
  - Manejo adecuado de excepciones y mensajes de error para identificar rápidamente problemas.

- **Configuración de FastAPI**
  - Inicialmente, los archivos se estaban subiendo incorrectamente debido a configuraciones en el código de FastAPI.
  - Se ajustaron los métodos de carga para asegurar que los datos se carguen correctamente a Snowflake.
  - Se detectó que al subir el archivo con `PUT @stage/filename`, Snowflake duplicaba el path del archivo (`stage/filename/filename.gz_uuid`), por lo que se modificó la ruta para evitar subcarpetas y subir directamente al root del stage.

### Soluciones Aplicadas

- Pruebas desde SQL worksheet de snowflake para validar formato y contenido de ficheros recibidos desde FastApi
- Parsear fichero JSON para adpatarlo al formato de fichero esperado por snowflake para carga en tabla (NDJSON)
- Ajustes en el código para eliminar compresiones innecesarias.
- Implementación de mensajes de log para facilitar la depuración y monitoreo.
- Captura del nombre real del archivo renombrado con UUID desde el resultado del comando de snowflake `PUT`, y uso correcto del path en el `COPY INTO`. En caso de que no se necesite paralelizar cargas de subida de archivos
- Corrección de la ruta del archivo en el `PUT` para evitar estructuras anidadas no deseadas en el stage.



### Próximos Pasos

- Implementación de AWS Lambda y API Gateway para hacer el sistema más escalable.
- Mover la logica de transformaciones y carga de datos a ecosistema snowflake (Actualmente se ejecuta desde fastapi usando el conector de snowflake) 
- Pruebas de carga y optimización del rendimiento para manejo de grandes volúmenes de datos.


## Preparación Inicial en Snowflake para el Primer Sprint

Antes de ejecutar la carga y procesamiento desde FastAPI, asegúrate de tener creados y validados los siguientes objetos en Snowflake:

### Creación de Formato de Archivo, Stage y Tabla

```sql
CREATE OR REPLACE FILE FORMAT json_as_variant
  TYPE = 'JSON'
  COMPRESSION = 'GZIP'
  STRIP_OUTER_ARRAY = FALSE
  ENABLE_OCTAL = FALSE
;

CREATE OR REPLACE STAGE leads_internal_stage
  FILE_FORMAT = json_as_variant;

CREATE OR REPLACE TABLE leads_raw (
    filename STRING,
    data VARIANT
);
```

### Consultas para Validar Objetos y Archivos en Stage (En este caso se usa un archivo del internal stage subido desde fastapi tmpq4lxyf6a_cleaned.json)

```sql
-- Ver contenido del stage
LIST @leads_internal_stage;

-- Consultar datos de la tabla leads_raw
SELECT * FROM leads_raw;
```

### Ejemplo de Carga Manual para Validar Copy Into

```sql
COPY INTO leads_raw(filename, data)
FROM (
    SELECT 'tmpq4lxyf6a_cleaned.json.gz' AS filename, $1
    FROM @leads_internal_stage/tmp0d0wpt2c_cleaned.json/tmp0d0wpt2c_cleaned.json.gz
)
FILE_FORMAT = (FORMAT_NAME = 'json_as_variant')
ON_ERROR = 'CONTINUE';

SELECT * FROM leads_raw;
```

### Consultas para Inspección de Archivos JSON en Stage

```sql
SELECT $1:Prospect_ID::STRING 
FROM @leads_internal_stage/tmpq4lxyf6a_cleaned.json/tmpq4lxyf6a_cleaned.json.gz (FILE_FORMAT => 'json_as_variant') 
LIMIT 10;
```

### Procedimiento Almacenado para Validar y Cargar JSON desde Stage

```sql
CREATE OR REPLACE PROCEDURE validate_and_load_json()
  RETURNS STRING
  LANGUAGE JAVASCRIPT
  EXECUTE AS CALLER
AS
$$
try {
    snowflake.createStatement({
        sqlText: `CREATE TEMPORARY TABLE IF NOT EXISTS temp_file_list (filename STRING, row_count NUMBER, column_count NUMBER)`
    }).execute();

    let fileList = snowflake.createStatement({
        sqlText: `SELECT DISTINCT METADATA$FILENAME AS filename FROM @leads_internal_stage LIMIT 1`
    }).execute();

    while (fileList.next()) {
        let filename = fileList.getColumnValue(1);

        try {
            let rowCount = snowflake.createStatement({
                sqlText: `SELECT COUNT(*) FROM @leads_internal_stage/${filename}`
            }).execute().getColumnValue(1);

            let columnCount = snowflake.createStatement({
                sqlText: `SELECT COUNT(*) FROM TABLE(INFER_SCHEMA(location=>'@leads_internal_stage/', pattern=>'${filename}'))`
            }).execute().getColumnValue(1);

            snowflake.createStatement({
                sqlText: `INSERT INTO temp_file_list (filename, row_count, column_count) VALUES ('${filename}', ${rowCount}, ${columnCount})`
            }).execute();

        } catch (error) {
            snowflake.createStatement({
                sqlText: `INSERT INTO temp_file_list (filename) VALUES ('${filename}')`
            }).execute();
            return `Error procesando archivo: ${filename} - ${error}`;
        }
    }

    let resultSet = snowflake.createStatement({
        sqlText: 'SELECT * FROM temp_file_list'
    }).execute();

    let result = '';
    while (resultSet.next()) {
        let filename = resultSet.getColumnValue(1);
        let rowCount = resultSet.getColumnValue(2) || 0;
        let columnCount = resultSet.getColumnValue(3) || 0;
        result += `Archivo: ${filename}, Filas: ${rowCount}, Columnas: ${columnCount}
`;
    }

    return result || 'Proceso completado sin errores';
} catch (e) {
    return `Error ejecutando el procedimiento: ${e}`;
}
$$;
```

### Consultas para Inspección y Carga Específica

```sql
SELECT 'tmpmcu1c5l6_cleaned.json.gz' AS filename, $1
FROM @leads_internal_stage/tmpmcu1c5l6_cleaned.json.gz;

SELECT 
    filename,
    data:"Prospect_ID"::STRING AS prospect_id
FROM leads_raw
LIMIT 10;

SELECT $1:"prospect_id" AS prospect_id
FROM @leads_internal_stage/tmprqsaeu0j_cleaned.json/tmprqsaeu0j_cleaned.json.gz
(FILE_FORMAT => json_as_variant)
LIMIT 5;
```
# 🛠️ Configuración del Entorno

Este proyecto requiere un archivo `.env` con variables de entorno específicas para conectarse a servicios como AWS (LocalStack) y Snowflake. A continuación, se describen los pasos para configurar y ejecutar correctamente el entorno.

---

## 📌 Prerrequisitos

Crea un archivo `.env` dentro de la carpeta `env/` con el siguiente contenido:

```env
# Archivo: env/.env

# Configuración de AWS y LocalStack
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3_ENDPOINT_URL=http://localstack:4566
S3_BUCKET=leads-bucket

# Credenciales de Snowflake (En el icono de perfil --> Account --> View account details)
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account_id
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=LEADS_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=SYSADMIN
```

---

## Componentes necesarios en Snowflake

| Componente         | Detalle                                       |
| ------------------ | --------------------------------------------- |
| Tabla en Snowflake | `leads_raw(filename STRING, data VARIANT)`    |
| Stage              | Apunta a bucket `leads-bucket` en LocalStack  |
| Snowpipe           | Carga desde `@mystage` usando `PARSE_JSON`    |
| FastAPI            | Subir a S3 y luego `REFRESH PIPE` manual      |
| Consulta           | Lee desde Snowflake y descompone el `VARIANT` |

---

## 🚀 Despliegue con Docker

Sigue estos pasos para levantar los servicios con Docker y cargar las variables de entorno desde el archivo `.env`:

1. Abre una terminal en la raíz del proyecto.
2. Ejecuta el siguiente comando:

```bash
docker-compose --env-file env/.env up --build
```

Esto levantará los contenedores usando las variables definidas en `env/.env`.

---

## 🛠 Configuración del Frontend en Codespaces

Si estás usando Codespaces para el frontend, sigue estos pasos para asegurarte de que Node.js y npm estén correctamente configurados:

### **1. Verificar si Node.js está Instalado**

Primero, verifica si Node.js está instalado:

```bash
node -v
npm -v
```

Si esto no devuelve un número de versión, significa que Node.js y npm no están instalados.

---

### **2. Instalar Node.js en Codespace**

Si no están instalados, puedes usar nvm (Node Version Manager) para instalar Node.js:

```bash
# Instalar nvm (si no está instalado)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash

# Cargar nvm en el terminal actual
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Verificar que nvm se instaló correctamente
nvm --version
```

Ahora instala Node.js usando nvm:

```bash
# Instalar la última versión LTS de Node.js
nvm install --lts

# Usar esta versión por defecto
nvm use --lts

# Verificar que Node.js y npm están instalados correctamente
node -v
npm -v
```

---

### **3. Instalar las Dependencias del Frontend**

Ahora puedes ir a la carpeta `frontend` y ejecutar:

```bash
cd frontend
npm install
```

---

### **4. Crear un Archivo `.nvmrc` (Opcional pero Recomendado)**

Para asegurarte de que siempre se use la misma versión de Node.js en tu proyecto, puedes crear un archivo `.nvmrc` en la raíz de tu proyecto con el siguiente contenido:

```
lts/*
```

---

### **5. Verificar el PATH (Si Todavía Hay Problemas)**

Si sigues teniendo problemas, asegúrate de que el PATH de nvm esté correctamente configurado. Puedes agregar esto a tu archivo `~/.bashrc`, `~/.zshrc` o `~/.bash_profile`:

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
```

Luego, recarga el perfil:

```bash
source ~/.bashrc  # o ~/.zshrc o ~/.bash_profile, dependiendo de tu shell
```


## ✅ Verificación de variables de entorno

1. Obtén el nombre del contenedor en ejecución:

```bash
docker ps
```

2. Accede al contenedor e imprime las variables de entorno:

```bash
docker exec -it <nombre_del_contenedor> env
```

3. Revisar los logs del contenedor:

```bash
docker logs <nombre_del_contenedor>
```

---


## 🧪 Comprobación rápida (opcional)

Puedes probar que la variable del bucket de S3 se carga correctamente ejecutando un comando dentro del contenedor (ejemplo):

```bash
echo $S3_BUCKET
```
Probar que aplicacion de fast api se ejecuta correctamente 
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Probar subida de archivo a través del endpoint /upload-and-load/ en FastAPI:
```bash
curl -X 'POST' 'http://0.0.0.0:8000/upload-and-load/' -F 'file=@/workspaces/lead-scoring-pipeline/data/SampleData.csv'

```
---

## 📅 Día 1: Preparación y Diseño del Sistema

### 1.1 Análisis del Proyecto y Requisitos

Tareas:

* Identificar los tipos de datos que necesitas procesar (leads, fuentes, puntuación).
* Definir las herramientas y tecnologías necesarias: Snowflake, AWS LocalStack, Python, ML Model, etc.

### 1.2 Definir la Arquitectura de la Solución

Arquitectura Propuesta:

* **Entrada de Datos (AWS LocalStack + S3)**: Los leads serán almacenados en archivos en S3 (simulado con LocalStack en tu entorno local). Los datos de cada lead estarán en formato JSON.
* **Procesamiento de Datos ( Snowflake UDF)**: Utilizar  una UDF en Snowflake para procesar cada lead.
* **Modelo de Scoring (ML)**: Crear un modelo básico de scoring usando Python o reglas simples.
* **Almacenamiento de Resultados (Snowflake)**: Los resultados del scoring se almacenarán en una tabla de Snowflake.
* **Interfaz de Consulta**: Una consulta SQL que permita al cliente revisar los resultados de los leads puntuados.

---

## 📅 Día 1: Desarrollo de la Funcionalidad Básica

### 2.1 Configuración del Entorno Local (AWS LocalStack + Snowflake)

Tareas:
* Configurar LocalStack para emular servicios de AWS S3 y Lambda.

* Configurar Snowflake 

* Configurar AWS SDK (Boto3) y librerías necesarias para interactuar con LocalStack y Snowflake.

* Crear un contenedor Docker para FastAPI que se conecte a LocalStack y Snowflake.

### 2.2 Desarrollo del Modelo de Scoring

* Desarrollar un modelo simple para calificar leads.
* Implementar reglas de negocio básicas para puntuar cada lead en función de su origen o características.

### 2.3 Implementación de la Función de Scoring (UDF)

* **Snowflake UDF**:

  *  UDF (función definida por el usuario) en Python que reciba los datos del lead (en formato JSON) y calcule la puntuación.

### 2.4 Cargar los Datos de Leads en AWS S3 (Simulado con LocalStack)

* Carga de  archivos de ejemplo de leads en S3 para simular el proceso. Cada archivo contendrá un JSON con los datos del lead.
* 
### 2.5 Servir Datos desde Snowflake a FastAPI

* Configurar FastAPI para conectarse a Snowflake y exponer endpoints para consultar los leads puntuados.
---

## 📅 Día 1: Ingesta y Procesamiento de Datos en Snowflake

### 3.1 Configuración de Snowpipe para Automatización

Pasos para configurar Snowpipe:

* Crear un **stage externo** en Snowflake apuntando al bucket de S3.
* Configurar **Snowpipe** para mover los datos automáticamente desde S3 a Snowflake.

### 3.2 Almacenamiento de Resultados en Snowflake

Crea una tabla en Snowflake para almacenar los resultados del scoring de los leads:

```sql
CREATE OR REPLACE TABLE leads (
    lead_id STRING,
    lead_name STRING,
    lead_source STRING,
    score FLOAT
);
```

### 3.3 Crear el Pipe para Snowpipe

```sql
CREATE OR REPLACE PIPE my_lead_pipe
  AUTO_INGEST = TRUE
  AS
  COPY INTO leads
  FROM @my_s3_stage
  FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"')
  ON_ERROR = 'CONTINUE';
```

* **AUTO\_INGEST = TRUE**: Hace que Snowpipe ingiera automáticamente los archivos tan pronto como se carguen en el bucket de S3.
* **COPY INTO leads**: Especifica que los datos deben ser cargados en la tabla leads.

### 3.4 Configurar Notificaciones en S3

* Configurar un evento de notificación en S3 para activar Snowpipe cuando se suban nuevos archivos al bucket.

### 3.5 Verificación y Pruebas

```sql
SELECT * FROM SNOWPIPE_LOAD_HISTORY WHERE PIPE_NAME = 'my_lead_pipe';
```

Verifica que los datos se están cargando correctamente.

---

## 📅 Día 4: Aplicación de Reglas de Scoring en Snowflake

### 4.1 Crear Procedimientos Almacenados para Scoring

```sql
CREATE OR REPLACE PROCEDURE apply_scoring()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    UPDATE leads
    SET score = CASE
        WHEN lead_source = 'Marketing' THEN 1
        ELSE 0
    END
    WHERE score IS NULL;
    RETURN 'Scoring applied successfully!';
END;
$$;
```

### 4.2 Crear Tarea Programada para Automatización

```sql
CREATE OR REPLACE TASK apply_scoring_task
WAREHOUSE = my_warehouse
SCHEDULE = 'USING CRON 0 * * * * UTC'
AS
CALL apply_scoring();
```

---

## ✅ Mejoras

* Integrar monitoreo y alertas para Snowpipe.
* Mejorar las reglas de scoring.
* Crear interfaz para visualizar los resultados.
* Automatizar despliegue con AWS SAM o Terraform.
