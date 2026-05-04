#!/bin/bash
set -e

echo "Building Docker images for CICD-Maturity project..."

# Build gateway
echo "Building gateway..."
docker build -t gateway:latest -f services/gateway/Dockerfile services/

# Build worker
echo "Building worker..."
docker build -t worker:latest -f services/worker/Dockerfile services/

echo "Images built successfully!"
echo ""
echo "To import into k3s:"
echo "  docker save gateway:latest | sudo k3s ctr images import -"
echo "  docker save worker:latest | sudo k3s ctr images import -"
