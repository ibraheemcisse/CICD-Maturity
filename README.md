# CI/CD Maturity

A distributed system demonstrating CI/CD pipeline evolution from basic to enterprise-grade.

## Architecture

Multi-service application:
- **Gateway**: FastAPI service handling incoming requests, rate limiting, circuit breaking
- **Worker**: Async job processor demonstrating backpressure and resource management
- **Queue**: Redis for async job distribution
- **Database**: PostgreSQL for persistence

## Stages

Each stage is a separate branch demonstrating pipeline maturity:

- **Stage 1 - Basic**: Build, test, push to registry
- **Stage 2 - Reliable**: Linting, caching, fail-fast
- **Stage 3 - Secure**: Security scanning (Gitleaks, Trivy, Semgrep)
- **Stage 4 - Trusted**: Image signing, SBOM, admission policies
- **Stage 5 - Enterprise**: OIDC, ArgoCD, runtime security

## Status

**Current**: Building foundation (Stage 0)

## Local Development

Requirements:
- Python 3.12+
- Docker
- k3s cluster

(Instructions will be added as services are built)
