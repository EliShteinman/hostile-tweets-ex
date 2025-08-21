docker buildx build --platform linux/amd64,linux/arm64 -t docker.io/a0533057932/fastapi-mongo-atlas:1.1.2 --push .
oc apply -f infra/