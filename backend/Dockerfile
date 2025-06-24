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

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de dependencias e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el contenido de backend (donde estás)
COPY . .

# Comando para Lambda
CMD ["app.main.handler"]
