# Lead Scoring Pipeline

## 📋 Objetivo del Proyecto

Crear una solución que reciba datos de leads, realice una puntuación (**scoring**) utilizando un modelo simple y almacene los resultados de manera estructurada en Snowflake. Esto incluye la ingesta de datos desde S3 (simulado con AWS LocalStack), el procesamiento del scoring y la automatización de la carga de datos.

---


# 🛠️ Configuración del Entorno

Este proyecto requiere un archivo `.env` con variables de entorno específicas para conectarse a servicios como AWS (LocalStack) y Snowflake. A continuación, se describen los pasos para configurar y ejecutar correctamente el entorno.

---

## 📁 Estructura esperada

Asegúrate de que el archivo `.env` esté ubicado dentro de una carpeta `env/` en la raíz del proyecto:

```
project-root/
│
├── env/
│   └── .env
├── docker-compose.yml
└── ...
```

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

# Credenciales de Snowflake
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account_id
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=LEADS_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=SYSADMIN
```

> 🛑 **Nota:** Reemplaza los valores como `your_user` y `your_password` con tus credenciales reales. Nunca subas este archivo a un repositorio público.

---

## 🚫 .gitignore recomendado

Asegúrate de que la carpeta `env/` y su contenido estén excluidos del control de versiones. Agrega lo siguiente a tu archivo `.gitignore`:

```gitignore
# Ignorar archivo de configuración sensible
env/.env
```

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

## ✅ Verificación de variables de entorno

Para asegurarte de que las variables de entorno se estén utilizando correctamente dentro del contenedor:

1. Obtén el nombre del contenedor en ejecución:

```bash
docker ps
```

2. Accede al contenedor e imprime las variables de entorno:

```bash
docker exec -it <nombre_del_contenedor> env
```

3. También puedes revisar los logs del contenedor:

```bash
docker logs <nombre_del_contenedor>
```

Busca las variables como `S3_ENDPOINT_URL` o `SNOWFLAKE_ACCOUNT` en la salida de los logs o del entorno.

---

## 🔐 Seguridad

- **No compartas el archivo `.env`.**
- **Usa un gestor de secretos si vas a desplegar en producción (ej. AWS Secrets Manager, Azure Key Vault, etc.).**
- **Revisa siempre que `env/.env` esté en el `.gitignore`.**

---

## 🧪 Comprobación rápida (opcional)

Puedes probar que la variable del bucket de S3 se carga correctamente ejecutando un comando dentro del contenedor (ejemplo):

```bash
echo $S3_BUCKET
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
