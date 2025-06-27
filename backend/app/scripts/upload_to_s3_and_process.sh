#!/bin/bash

# Script para subir archivo grande a S3 vía presigned URL y notificar backend

if [ -z "$1" ]; then
  echo "Uso: $0 ruta/al/archivo"
  exit 1
fi

FILEPATH="$1"
FILENAME=$(basename "$FILEPATH")
CONTENT_TYPE=$(file --mime-type -b "$FILEPATH")

API_BASE="https://9muoh3ge72.execute-api.eu-west-1.amazonaws.com"

echo "1. Solicitando URL presigned para subir $FILENAME..."
RESPONSE=$(curl -s -G "$API_BASE/generate-presigned-url/" --data-urlencode "filename=$FILENAME" --data-urlencode "content_type=$CONTENT_TYPE")

URL=$(echo "$RESPONSE" | jq -r '.url')
KEY=$(echo "$RESPONSE" | jq -r '.key')

if [ "$URL" == "null" ] || [ -z "$URL" ]; then
  echo "Error obteniendo URL presigned:"
  echo "$RESPONSE"
  exit 1
fi

echo "2. Subiendo archivo a S3..."
curl -s -X PUT "$URL" -T "$FILEPATH" -H "Content-Type: $CONTENT_TYPE"

if [ $? -ne 0 ]; then
  echo "Error al subir archivo a S3"
  exit 1
fi

echo "3. Notificando backend para procesar archivo..."
NOTIFY_RESPONSE=$(curl -s -X POST "$API_BASE/process-s3-file/" -H "Content-Type: application/json" -d "{\"s3_key\": \"$KEY\"}")

echo "Respuesta backend:"
echo "$NOTIFY_RESPONSE"
