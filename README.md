 Lead Scoring Pipeline

## 📋 Objetivo del Proyecto

Crear una solución que reciba datos de leads, realice una puntuación (**scoring**) utilizando un modelo simple y almacene los resultados de manera estructurada en Snowflake. Esto incluye la ingesta de datos desde S3 (, el procesamiento del scoring y la automatización de la carga de datos.

---

## 📈 Iterative Development – Sprints Overview (📅 Agile Sprint Plan). 2 Días

### Sprint 1 - Procesamiento de Leads

#### Funcionalidades Implementadas

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

#### Consideraciones Técnicas para la Carga y Procesamiento de Datos

1. **Separación de Tablas**
   - leads_raw: tabla intermedia que almacena los datos en formato JSON crudo.
   - leads_final: tabla destino con los datos desplegados en columnas estructuradas.

2. **Carga Incremental**
   - Comparación por identificadores únicos como Prospect_ID.
   - Uso de campos de fecha de actualización o generación de hash/checksum.

3. **Automatización del Flujo**
   - **Procedimientos Almacenados (PA):** lógica de validación de ficheros y creacion de tabla a partir de estructura de fichero JSON cargado en internal stage
   - **TASK:** Carga datos en tabla leads_final.
   - **STREAMs:** detectan nuevos registros en tabla leads_raw y activa task de carga en tabla final.
   - **Snowpipe:** automatiza la ingesta continua.

> Estas consideraciones permitirán escalar el pipeline de forma robusta, controlada y optimizada para entornos de producción.

#### Problemas Encontrados

- **Errores de Compresión y Formato**
  - Archivos subidos como .json.gz causaban errores.
  - Configuración corregida para evitar errores de conteo de filas y columnas.
  - Snowflake renombraba automáticamente los archivos, dificultando su carga con COPY INTO.

- **Errores en Procedimientos Almacenados**
  - Ajustes de sintaxis y lógica en procedimientos.
  - Mejor manejo de excepciones y mensajes de error.

- **Configuración de FastAPI**
  - Archivos mal subidos por configuraciones incorrectas.
  - Ajuste de rutas para evitar subcarpetas en stages.

#### Soluciones Aplicadas

- Validación desde Snowflake SQL worksheet.
- Conversión de JSON a NDJSON.
- Eliminación de compresión innecesaria.
- Captura del nombre renombrado con UUID tras el comando PUT.
- Ruta correcta en PUT y COPY INTO. Finalmente, se opta por el siguiente flujo de datos : Snowpipe carga en leads_raw  datos de JSON→ (detected by STREAM) → TASK → inserta en leads_finalleads_raw → (detected by STREAM) → TASK → inserta en leads_final


#### 📊 Dashboard de Leads

Este proyecto incluye un panel de visualización frontend en React, conectado a un backend FastAPI y una base de datos en Snowflake.

##### 🖥️ Interfaz del Dashboard de Leads

El frontend de la aplicación proporciona un dashboard interactivo con un panel lateral y múltiples secciones visuales para la gestión de leads. Está construido en React y se conecta al backend para visualizar, puntuar y explorar datos directamente desde Snowflake.

##### Características principales

- 📊 Gráficos de desempeño y fuentes de leads
- 📋 Vista tabular de los datos cargados
- 🧠 Panel de scoring automático para leads


![image](https://github.com/user-attachments/assets/39bd3cc2-cd1c-4208-8bef-73be3da3d5c5)


> La imagen anterior representa la vista "Gráficos", donde se muestran análisis visuales sobre puntuación, conversión y actividad de los leads.

---

#### Próximos Pasos

- Implementar AWS Lambda y API Gateway.
- Mover lógica de transformación a Snowflake.
- Pruebas de carga y optimización del rendimiento.

---

## 🧱 Preparación Inicial en Snowflake

### Creación de Formato de Archivo, Stage y Tabla

```sql
CREATE OR REPLACE FILE FORMAT json_as_variant
  TYPE = 'JSON'
  COMPRESSION = 'GZIP'
  STRIP_OUTER_ARRAY = FALSE
  ENABLE_OCTAL = FALSE;

CREATE OR REPLACE STAGE leads_internal_stage
  FILE_FORMAT = json_as_variant;

CREATE OR REPLACE TABLE leads_raw (
    filename STRING,
    data VARIANT
);
```

### Consultas para Validar Objetos y Archivos en Stage

```sql
LIST @leads_internal_stage;
SELECT * FROM leads_raw;
```

### Ejemplo de Carga Manual para Validar COPY INTO

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

### Consultas para Inspección de Archivos JSON

```sql
SELECT $1:Prospect_ID::STRING 
FROM @leads_internal_stage/tmpq4lxyf6a_cleaned.json/tmpq4lxyf6a_cleaned.json.gz 
(FILE_FORMAT => 'json_as_variant') 
LIMIT 10;
```

### Procedimiento Almacenado para Validar y Cargar JSON

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

---

## 🛠️ Configuración del Entorno

Este proyecto requiere un archivo `.env` con variables de entorno específicas para conectarse a servicios como AWS (LocalStack) y Snowflake.

---

## 📌 Prerrequisitos

Crea un archivo `.env` dentro de la carpeta `env/` con el siguiente contenido:

```env
# Archivo: env/.env

# Configuración de AWS y LocalStack
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3_ENDPOINT_URL=http://localstack:4566
S3_BUCKET=your-bucket-name

# Credenciales de Snowflake
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account_id
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=LEADS_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=SYSADMIN
```

## Componentes necesarios en Snowflake

| Componente         | Detalle                                       |
| ------------------ | --------------------------------------------- |
| Tabla en Snowflake | `leads_raw(filename STRING, data VARIANT)`    |
| Stage              | Apunta a bucket `your-bucket-name` en LocalStack  |
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

# 🚀 Sprint 2: Arquitectura Serverless e Integración en AWS

Como parte de la evolución del proyecto, se implementó una arquitectura serverless completa en AWS, integrando Snowflake, Lambda, API Gateway, S3, CloudFront y otros servicios clave.

---

### ✅ Mejoras en el Backend (FastAPI + AWS Lambda)

- Se adaptó el backend construido con **FastAPI** para ejecutarse en **AWS Lambda** mediante contenedores (Docker) y `Mangum`.
- Se estructuró la carga segura de variables con un archivo `.env` dentro de `app/env/.env`.
- Se refactorizó el `Dockerfile` para incluir solo dependencias necesarias y reducir el peso de la imagen.
- Se conectó correctamente Lambda a Snowflake para operaciones SQL, `PUT` y Snowpipe.
- Se expusieron endpoints como `/leads`, `/upload`, `/score-lead` y `/lead-count` a través de **API Gateway**.

---

### 🌐 Mejora del Frontend (S3 + CloudFront)

- Se desplegó el frontend como sitio estático en **Amazon S3**.
- Se creó una distribución de **CloudFront** para servir el sitio globalmente con mejor performance.
- Se habilitó **CORS** en el backend para aceptar peticiones desde CloudFront y otros orígenes permitidos.

---

### 🧩 Diagnóstico del Problema

#### ❌ Problema Inicial:
Al invocar una función Lambda construida como imagen Docker (basada en `public.ecr.aws/lambda/python:3.11`) que contiene una aplicación FastAPI adaptada con Mangum:

- Todas las peticiones (como `GET /`) devolvían **404 Not Found** al probar localmente vía Docker.
- Sin embargo, ejecutando la misma app con `uvicorn` funcionaba correctamente.
- Para evitar consumir la capa gratuita de AWS Lambda, se decidió probar localmente con **SAM**.

---

### ✅ Causa Raíz

Las imágenes contenedor de Lambda **no ejecutan un servidor web** como `uvicorn`. En su lugar, esperan una **función handler** con el formato `modulo.función`, la cual es invocada por API Gateway u otros eventos Lambda.

Por eso, aunque tu FastAPI funcionaba bien con `uvicorn`, no respondía cuando era invocada por Lambda sin el adaptador adecuado.

---

### 🔧 Pasos de Solución

#### 1. ✅ Estructura correcta en `main.py` con Mangum

 Lambda no entiende directamente las aplicaciones ASGI como FastAPI. Para adaptarlas, se usa **Mangum**, un adaptador que convierte los eventos de Lambda en peticiones compatibles con FastAPI.

```python
from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello from Lambda"}

handler = Mangum(app)
```

Esto asegura que la función `handler` pueda ser invocada correctamente por Lambda.

---

#### 2. ✅ Dockerfile

 Lambda espera que el código esté en `/var/task` y que la imagen defina un `CMD` que apunte al handler. También es necesario instalar las dependencias del sistema y de Python en la imagen.

```dockerfile
FROM public.ecr.aws/lambda/python:3.11

RUN yum install -y gcc gcc-c++ make libffi-devel python3-devel

WORKDIR /var/task

COPY requirements.txt .
RUN python3 -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

CMD ["app.main.handler"]
```

Esto asegura que la Lambda encuentre el módulo `app.main` y su función `handler`.

---

#### 3. ✅ Archivo `.dockerignore`

Al construir imágenes Docker, incluir archivos innecesarios (como archivos temporales, datos o configuraciones) puede romper el build o aumentar el tamaño de la imagen.

Se añadió un archivo `.dockerignore` para excluir archivos no necesarios:

```
__pycache__/
*.py[cod]
data/
*.env
.sam/
.aws-sam/
```

Esto evita errores de acceso y mejora la eficiencia del build.

---

#### 4. ✅ `template.yaml` para SAM

`template.yaml` define los recursos que SAM usará para simular la arquitectura en local o desplegarla en AWS. Se configura el timeout, el tipo de paquete (`Image`) y el punto de entrada.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Resources:
  FastApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      Timeout: 10
      Architectures:
        - x86_64
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /
            Method: get
    Metadata:
      Dockerfile: Dockerfile
      DockerContext: .
      DockerTag: fastapi-lambda
```

Así SAM puede construir y ejecutar la función localmente como si estuviera en AWS.

---
### ⚙️ ¿Qué es AWS SAM?

**AWS SAM (Serverless Application Model)** es un framework open-source para desarrollar, probar y desplegar aplicaciones serverless como AWS Lambda.

> Teoría: SAM usa Docker para emular localmente la ejecución de funciones Lambda, incluyendo eventos HTTP, cron, S3, etc. Es ideal para desarrollo sin consumir AWS.

#### ✅ Ventajas principales:
- Probar funciones Lambda **localmente** con `sam local invoke` o `sam local start-api`.
- Evitar consumir la capa gratuita de AWS.
- Facilita el despliegue a producción con `sam deploy`.

---

### 🚀 Cómo probar localmente

# 🧪 Pruebas locales de endpoints con SAM + script .sh

Este archivo explica **por qué y cómo** automatizar las pruebas de tus endpoints cuando ejecutas tu aplicación FastAPI sobre AWS Lambda **usando `sam local start-api`**.

---

## ✅ ¿Por qué hacer pruebas locales?

Cuando desarrollas una API serverless con FastAPI + Lambda, es común cometer errores de:

- rutas no registradas en `template.yaml`
- errores de CORS o de conexión
- estructura incorrecta del handler
- falta de parámetros obligatorios

Automatizar las pruebas con un script `.sh` permite verificar rápidamente que todos los endpoints:

- están disponibles
- responden correctamente
- no devuelven errores 403 o 500

---

## 🚀 PRuebas de endpoints localmente

Se crea un script llamado `tests_endpoints.sh` que lanza peticiones `curl` a cada endpoint y muestra claramente:

- la URL probada
- el contenido de la respuesta
- el código de estado HTTP

---


## ▶️ Cómo ejecutarlo

1. Asegúrate de tener la app corriendo:

```bash
sam local start-api
```

2. En otra terminal, dale permisos al script y ejecútalo:

```bash
chmod +x tests/test_all.sh
./tests/test_all.sh
```

---

## ✅ Resultado esperado

```
🔹 Testing / (/)
{"message":"Hello from Lambda"}
Status: 200
-----------------------------
🔹 Testing /healthcheck (/healthcheck)
{"status":"ok"}
Status: 200
-----------------------------
...
```

---

## 🧠 Conclusión

El uso de un script `.sh` para pruebas locales con `sam local` es una forma rápida, ligera y efectiva de validar el comportamiento de tus endpoints **antes de desplegar a AWS**, asegurando que:

- la configuración de rutas esté correcta
- tu función handler funcione como se espera
- la integración con Snowflake, S3 y SageMaker se pueda probar paso a paso



```bash
# Construir la imagen
sam build --use-container

# Iniciar emulación local de API Gateway
sam local start-api

# Luego acceder a:
http://127.0.0.1:3000/
```

Esto inicia la función Lambda con una interfaz local de API Gateway.

---

### ✅ Resultado Final

- Lambda se ejecuta localmente vía Docker y responde a las solicitudes correctamente.
- Se eliminan errores 404.
- No se incurre en costos de uso de AWS para pruebas locales.


### ⚙️ Despliegue con AWS CLI

#### 🔹 Crear repositorio en ECR:
```bash
aws ecr create-repository --repository-name lead-scoring-api --region your-region
```

#### 🔹 Login e imagen Docker:
```bash
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com
docker build -t lead-scoring-api .
docker tag lead-scoring-api:latest your-account-id.dkr.ecr.your-region.amazonaws.com/lead-scoring-api:latest
docker push your-account-id.dkr.ecr.your-region.amazonaws.com/lead-scoring-api:latest
```

#### 🔹 Crear función Lambda desde imagen:
```bash
aws lambda create-function --function-name lead-scoring-api \
  --package-type Image \
  --code ImageUri=your-account-id.dkr.ecr.your-region.amazonaws.com/lead-scoring-api:latest \
  --role arn:aws:iam::your-account-id:role/lambda-execution-role \
  --region your-region --timeout 60 --memory-size 1024
```

#### 🔹 API Gateway conectado a Lambda:
```bash
aws apigatewayv2 create-api \
  --name lead-scoring-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:your-region:your-account-id:function:lead-scoring-api
```

#### 🔹 Hosting frontend en S3 + CloudFront:
```bash
aws s3 create-bucket --bucket your-frontend-bucket --region your-region
aws s3 website s3://your-frontend-bucket/ --index-document index.html
aws s3 sync ./frontend/build/ s3://your-frontend-bucket/
aws cloudfront create-distribution --origin-domain-name your-frontend-bucket.s3-website-your-region.amazonaws.com
```
Obtener id de distribucion de Cloudfront
```bash
aws cloudfront list-distributions \
  --query "DistributionList.Items[*].{Id:Id,DomainName:DomainName}" \
  --output table
```
---


#### 🔹Payload de prueba para AWS Lambda:

```bash
 {
  "version": "2.0",
  "routeKey": "GET /leads/",
  "rawPath": "/leads/",
  "rawQueryString": "",
  "headers": {
    "host": "localhost",
    "user-agent": "aws-cli/2.0",
    "x-forwarded-for": "127.0.0.1"
  },
  "requestContext": {
    "http": {
      "method": "GET",
      "path": "/leads/",
      "protocol": "HTTP/1.1",
      "sourceIp": "127.0.0.1",
      "userAgent": "aws-cli/2.0"
    }
  },
  "isBase64Encoded": false
} 
```

### Habilitar onfiguración de sitio web estático en bucket
```bash 
aws s3 website s3://your-frontend-bucket/ --index-document index.html --error-document index.html
```
---

### 🔓 Permitir acceso público al frontend en S3

Para que CloudFront (o cualquier navegador) pueda servir tu frontend almacenado en S3, debes asegurarte de que los archivos sean públicamente accesibles. Esto se logra aplicando una política de bucket que permita lecturas anónimas.

#### 🛠️ Comando para aplicar política pública al bucket

```bash
aws s3api put-bucket-policy --bucket your-frontend-bucket --policy file://<(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-frontend-bucket/*"
    }
  ]
}
EOF
)
```

## 🚀 Despliegue de Frontend (Lead Scoring)

Cada vez que se modifica el código del frontend, ejecutar los siguientes comandos para actualizar el entorno en producción (S3 + CloudFront):

```bash
# 1. Generar la build del frontend
npm run build

# 2. Subir la carpeta 'build/' al bucket de S3
aws s3 sync ./build/ s3://your-frontend-bucket --delete

# 3. (Solo si es necesario) Configurar el bucket como sitio web estático
aws s3 website s3://your-frontend-bucket/ --index-document index.html

# 4. Invalidar caché de CloudFront para aplicar cambios
aws cloudfront create-invalidation \
  --distribution-id <your-distribution-id> \
  --paths "/*"
```
### Payload para probar AWS Lambda desde consola 

```json
{
  "version": "2.0",
  "routeKey": "GET /healthcheck",
  "rawPath": "/healthcheck",
  "rawQueryString": "",
  "headers": {
    "host": "your-api-id.execute-api.your-region.amazonaws.com",
    "user-agent": "curl/7.64.1",
    "accept": "*/*"
  },
  "requestContext": {
    "http": {
      "method": "GET",
      "path": "/healthcheck",
      "protocol": "HTTP/1.1",
      "sourceIp": "127.0.0.1",
      "userAgent": "curl/7.64.1"
    }
  },
  "isBase64Encoded": false
}
```

## Integración Snowflake con AWS S3 usando Storage Integration y rol IAM

Este procedimiento describe cómo configurar un bucket S3 con permisos para que Snowflake pueda cargar datos mediante Snowpipe usando una Storage Integration segura.

### 1. Crear bucket S3

Crea un bucket en AWS S3 donde se subirán los archivos, por ejemplo:

```bash
aws s3api create-bucket --bucket your-bucket-name --region your-region --create-bucket-configuration LocationConstraint=your-region
````

### 2. Crear rol IAM en AWS con permisos al bucket

* Crea un rol IAM llamado, por ejemplo, `SnowflakeS3AccessRole`.
* Asigna una política de confianza temporal para poder crear el rol (luego se actualizará).
* Añade una política inline con permisos:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::your-bucket-name",
        "arn:aws:s3:::your-bucket-name/*"
      ]
    }
  ]
}
```

### 3. Crear Storage Integration en Snowflake

Ejecuta el siguiente SQL en Snowflake, reemplazando `<ROL_ARN>` por el ARN completo del rol creado en AWS:

```sql
CREATE OR REPLACE STORAGE INTEGRATION s3_leads_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = S3
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = '<ROL_ARN>'
  STORAGE_ALLOWED_LOCATIONS = ('s3://your-bucket-name/');
```

### 4. Obtener parámetros para la política de confianza

Ejecuta:

```sql
DESC INTEGRATION s3_leads_integration;
```

Anota los valores:

* `STORAGE_AWS_IAM_USER_ARN`
* `STORAGE_AWS_EXTERNAL_ID`

### 5. Actualizar política de confianza en AWS IAM

Edita la política de confianza del rol `SnowflakeS3AccessRole` para que luzca así, usando los valores obtenidos:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "<STORAGE_AWS_IAM_USER_ARN>"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "<STORAGE_AWS_EXTERNAL_ID>"
        }
      }
    }
  ]
}
```

### 6. Crear stage en Snowflake

```sql
CREATE OR REPLACE STAGE leads_internal_stage
  URL = 's3://your-bucket-name/'
  STORAGE_INTEGRATION = s3_leads_integration
  FILE_FORMAT = json_as_variant;
```




### 🧠 Servicios y funcionalidades integradas

- **Snowflake**: Carga de datos, funciones de scoring, tareas programadas.
- **AWS Lambda**: Backend sin servidores.
- **API Gateway**: Exposición de endpoints públicos.
- **Amazon S3 + CloudFront**: Hosting global del frontend.
- **AWS SageMaker**: Scoring predictivo de leads.
- **AWS Athena**: Conteo de registros desde datos crudos en S3.
- **AWS CloudWatch**: Monitoreo de logs.
- **PowerCurve (futuro)**: Considerado para administración avanzada de usuarios.

