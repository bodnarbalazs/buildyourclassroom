#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: ./deploy.sh <version-tag> (e.g. v1.0.0)}"

ACR_REGISTRY="${ACR_REGISTRY:?Set ACR_REGISTRY env var}"
ACR_USERNAME="${ACR_USERNAME:?Set ACR_USERNAME env var}"
ACR_PASSWORD="${ACR_PASSWORD:?Set ACR_PASSWORD env var}"

echo "==> Deploying ${VERSION} to ${ACR_REGISTRY}"

# Build images
echo "==> Building Docker images..."
docker build -t "${ACR_REGISTRY}/api:${VERSION}"          -f docker/api.Dockerfile .
docker build -t "${ACR_REGISTRY}/frontend:${VERSION}"     -f docker/frontend.Dockerfile .
docker build -t "${ACR_REGISTRY}/microservice:${VERSION}" -f docker/microservice.Dockerfile src/microservices/microservice
docker build -t "${ACR_REGISTRY}/worker:${VERSION}"       -f docker/worker.Dockerfile src/microservices/microservice

# Authenticate to ACR
echo "==> Logging in to ACR..."
docker login "${ACR_REGISTRY}" -u "${ACR_USERNAME}" -p "${ACR_PASSWORD}"

# Push images
echo "==> Pushing images to ACR..."
docker push "${ACR_REGISTRY}/api:${VERSION}"
docker push "${ACR_REGISTRY}/frontend:${VERSION}"
docker push "${ACR_REGISTRY}/microservice:${VERSION}"
docker push "${ACR_REGISTRY}/worker:${VERSION}"

# Generate k8s manifests via Aspire publisher
echo "==> Generating Kubernetes manifests..."
aspire publish --project src/backend/Hackathon.AppHost -o k8s/

# Apply manifests
echo "==> Applying manifests to cluster..."
kubectl apply -f k8s/

# Wait for rollout
echo "==> Waiting for rollouts..."
kubectl rollout status deployment/api --timeout=120s
kubectl rollout status deployment/frontend --timeout=120s
kubectl rollout status deployment/microservice --timeout=120s
kubectl rollout status deployment/worker --timeout=120s

echo "==> Deploy ${VERSION} complete"
