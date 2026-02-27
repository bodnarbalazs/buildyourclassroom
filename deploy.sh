#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: ./deploy.sh <version-tag> (e.g. v1.0.0)}"

# Read ACR login server from env or terraform output
ACR_LOGIN_SERVER="${ACR_LOGIN_SERVER:-$(cd infra && terraform output -raw acr_login_server)}"

echo "==> Deploying ${VERSION} to ${ACR_LOGIN_SERVER}"

# Build images
echo "==> Building Docker images..."
docker build -t "${ACR_LOGIN_SERVER}/api:${VERSION}"          -f docker/api.Dockerfile .
docker build -t "${ACR_LOGIN_SERVER}/frontend:${VERSION}"     -f docker/frontend.Dockerfile .
docker build -t "${ACR_LOGIN_SERVER}/microservice:${VERSION}" -f docker/microservice.Dockerfile src/microservices/microservice
docker build -t "${ACR_LOGIN_SERVER}/worker:${VERSION}"       -f docker/worker.Dockerfile src/microservices/microservice

# Authenticate to ACR
echo "==> Logging in to ACR..."
az acr login --name "${ACR_LOGIN_SERVER}"

# Push images
echo "==> Pushing images to ACR..."
docker push "${ACR_LOGIN_SERVER}/api:${VERSION}"
docker push "${ACR_LOGIN_SERVER}/frontend:${VERSION}"
docker push "${ACR_LOGIN_SERVER}/microservice:${VERSION}"
docker push "${ACR_LOGIN_SERVER}/worker:${VERSION}"

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
