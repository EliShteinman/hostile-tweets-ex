oc delete all,secrets,configmap --selector app.kubernetes.io/part-of=mongo-tweets-app
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
echo "API Documentation: https://${ROUTE_URL}/docs"
