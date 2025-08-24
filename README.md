# Malicious Text Analysis API

## What it does
Analyzes texts for weapons, sentiment, and rare words.

## Quick Start
```bash
pip install -r requirements.txt

# Set environment variables
export MONGO_ATLAS_URI="mongodb+srv://IRGC:iraniraniran@iranmaldb.gurutam.mongodb.net/"
export MONGO_DB_NAME="IranMalDB"
export MONGO_COLLECTION_NAME="tweets"

# Run
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Endpoints
- `GET /` - Health container check
- `GET /health` - Health software check
- `GET /data` - Raw data
- `GET /data-proses` - Processed data

## Output Format
```json
[
  {
    "id": "64fcf0d2a1b23c0012345678",
    "original_text": "Tomorrow we attack using gun",
    "rarest_word": "Tomorrow",
    "sentiment": "negative",
    "weapons_detected": "gun"
  }
]
```

## Docker
```bash
docker build -t text-analyzer .
docker run -p 8080:8080 \
  -e MONGO_ATLAS_URI="mongodb+srv://IRGC:iraniraniran@iranmaldb.gurutam.mongodb.net/" \
  -e MONGO_DB_NAME="IranMalDB" \
  -e MONGO_COLLECTION_NAME="tweets" \
  text-analyzer
```

## OpenShift
```bash
export DOCKERHUB_USERNAME='your-dockerhub-username'
export IMAGE_TAG="demo-$(date +%s)"
export FULL_IMAGE_NAME="docker.io/${DOCKERHUB_USERNAME}/fastapi-mongo-atlas:${IMAGE_TAG}"

docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t "${FULL_IMAGE_NAME}" --push .

oc apply -f infra/configmap.yaml
oc apply -f infra/secrets.yaml
sed -e "s|docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-atlas:latest|${FULL_IMAGE_NAME}|g" \
    "infra/deployment.yaml" | oc apply -f -
oc apply -f infra/service.yaml
oc apply -f infra/route.yaml

export ROUTE_URL=$(oc get route mongo-atlas-route -o jsonpath='{.spec.host}')
echo "Application URL: https://${ROUTE_URL}"
```