# # Utilizar una imagen base para FastAPI
# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

# # Establecer el directorio de trabajo
# WORKDIR /app

# # Copiar el archivo de dependencias
# COPY requirements.txt /app/

# # Instalar las dependencias
# RUN pip install --no-cache-dir -r requirements.txt

# # Copiar el código de la aplicación FastAPI
# COPY ./app /app/

# # Exponer el puerto para la API
# EXPOSE 80

# # Comando para ejecutar FastAPI con Uvicorn
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
FROM public.ecr.aws/lambda/python:3.11

# Instala herramientas del sistema necesarias para compilar paquetes
RUN yum install -y gcc gcc-c++ make libffi-devel python3-devel

# Lambda busca los archivos en /var/task
WORKDIR /var/task

COPY requirements.txt .

# Actualiza pip y luego instala requirements
RUN python3 -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 👇 Copia correctamente la carpeta 'app' al lugar correcto
COPY app/ app/

# Lambda ejecutará handler en app/main.py
CMD ["app.main.handler"]
