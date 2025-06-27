#!/bin/bash

BASE_URL="http://127.0.0.1:3000"
FILENAME="SampleData.csv"
CONTENT_TYPE="text/csv"
LOCAL_FILE_PATH="data/$FILENAME"

function test_endpoint() {
  local ENDPOINT=$1
  local LABEL=$2
  echo "🔹 Testing $LABEL ($ENDPOINT)"
  RESPONSE=$(curl -s -w "\\nStatus: %{http_code}\\n" "$BASE_URL$ENDPOINT")
  echo -e "$RESPONSE"
  echo "-----------------------------"
}

# Test base endpoints
test_endpoint "/" "/"
test_endpoint "/healthcheck" "/healthcheck"
test_endpoint "/score-all-leads" "/score-all-leads"
test_endpoint "/generate-presigned-url?filename=test.csv&content_type=text/csv" "/generate-presigned-url"

# Upload SampleData.csv via presigned URL
echo "🔹 Testing S3 upload flow for $FILENAME"

if [ ! -f "$LOCAL_FILE_PATH" ]; then
  echo "❌ File not found: $LOCAL_FILE_PATH"
  exit 1
fi

echo "➡️ Getting presigned URL..."
PRESIGNED_RESPONSE=$(curl -s "$BASE_URL/generate-presigned-url?filename=$FILENAME&content_type=$CONTENT_TYPE")

URL=$(echo "$PRESIGNED_RESPONSE" | jq -r '.url')
KEY=$(echo "$PRESIGNED_RESPONSE" | jq -r '.key')

if [[ "$URL" == "null" || -z "$URL" ]]; then
  echo "❌ Failed to get presigned URL"
  echo "$PRESIGNED_RESPONSE"
  exit 1
fi

echo "✅ Presigned URL obtained. Uploading file to S3..."
UPLOAD_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$URL" \
  -H "Content-Type: $CONTENT_TYPE" \
  --data-binary @"$LOCAL_FILE_PATH")

if [[ "$UPLOAD_RESPONSE" == "200" || "$UPLOAD_RESPONSE" == "204" ]]; then
  echo "✅ File uploaded successfully to S3."
else
  echo "❌ Upload failed. HTTP status: $UPLOAD_RESPONSE"
  exit 1
fi

echo "➡️ Calling /process-s3-file for key: $KEY"
PROCESS_RESPONSE=$(curl -s -X POST "$BASE_URL/process-s3-file" \
  -H "Content-Type: application/json" \
  -d "{\"s3_key\": \"$KEY\"}")

echo "✅ Process response:"
echo "$PROCESS_RESPONSE"
