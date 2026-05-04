#!/bin/bash
set -e

echo "Building Docker images for CICD-Maturity project..."

# Build gateway
echo "Building gateway..."
docker build -t gateway:latest \
  --build-arg SERVICE=gateway \
  -f services/gateway/Dockerfile \
  .

# Build worker
echo "Building worker..."
docker build -t worker:latest \
  --build-arg SERVICE=worker \
  -f services/worker/Dockerfile \
  .

echo "Images built successfully!"
echo ""
echo "To import into k3s:"
echo "  docker save gateway:latest | sudo k3s ctr images import -"
echo "  docker save worker:latest | sudo k3s ctr images import -"
