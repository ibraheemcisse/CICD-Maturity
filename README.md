# CI/CD Maturity

A distributed system demonstrating CI/CD pipeline evolution from basic to enterprise-grade.

## Architecture
┌─────────────────────────────────────────────────────────────┐
│                      k3s Cluster                             │
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Gateway    │────────▶│    Worker    │                 │
│  │  (FastAPI)   │         │  (FastAPI)   │                 │
│  │              │         │              │                 │
│  │ • Rate limit │         │ • Job proc   │                 │
│  │ • Circuit    │         │ • OOM sim    │                 │
│  │   breaker    │         │ • Backpress  │                 │
│  └──────┬───────┘         └──────┬───────┘                 │
│         │                        │                          │
│         │                        │                          │
│         ├────────────────────────┼──────────┐              │
│         │                        │          │              │
│         ▼                        ▼          ▼              │
│  ┌──────────────┐         ┌──────────────┐ ┌─────────┐   │
│  │  PostgreSQL  │         │    Redis     │ │ Metrics │   │
│  │ (StatefulSet)│         │   (Queue)    │ │ (Future)│   │
│  └──────────────┘         └──────────────┘ └─────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
External → Gateway (Ingress: gateway.local)

**Multi-service distributed job processing system:**

- **Gateway**: FastAPI service handling job submissions with circuit breaker for queue failures
- **Worker**: Async job processor with concurrency limits and backpressure detection
- **Redis Queue**: Job distribution between gateway and workers
- **PostgreSQL**: Job persistence (future integration)

**Demonstrates production failure patterns:**
- Circuit breaking (protects against cascading failures)
- OOM simulation (demonstrates resource exhaustion under load)
- Backpressure handling (queue depth monitoring + worker concurrency limits)

## Why This Architecture

This is the **Stripe/GitHub/Shopify pattern** — gateway → queue → worker pool. Real companies use this exact architecture at scale. This project demonstrates:

1. How to build it correctly
2. How to instrument it for observability
3. How failures propagate and how to contain them
4. How CI/CD matures as the system grows

## Project Structure
cicd-maturity/
├── services/
│   ├── gateway/          # API gateway service
│   ├── worker/           # Job processing service
│   └── shared/           # Shared models, queue client, config
├── infrastructure/       # Kubernetes manifests
│   ├── postgres/         # PostgreSQL StatefulSet
│   ├── redis/            # Redis deployment
│   ├── gateway-deployment.yaml
│   ├── worker-deployment.yaml
│   └── ingress.yaml
└── .github/workflows/    # CI/CD pipelines (future stages)

## CI/CD Pipeline Stages

Each stage is a separate branch demonstrating pipeline maturity evolution:

### **Stage 1 - Basic** (Planned)
- Build Docker images for gateway + worker
- Run basic tests
- Push to GitHub Container Registry
- Deploy to k3s

### **Stage 2 - Reliable** (Planned)
- Linting (ruff, mypy)
- Dependency caching
- Fail-fast behavior
- Integration tests across services

### **Stage 3 - Secure** (Planned)
- Gitleaks (secrets scanning)
- Trivy (container vulnerability scanning)
- Semgrep (SAST)
- Checkov (IaC security)

### **Stage 4 - Trusted** (Planned)
- Cosign (image signing)
- Syft (SBOM generation)
- Kyverno (admission policies)

### **Stage 5 - Enterprise** (Planned)
- GitHub Actions OIDC (keyless auth)
- ArgoCD GitOps deployment
- Falco runtime security
- Manual approval gates

## Local Development

### Prerequisites

- Python 3.12+
- Docker
- k3s cluster
- Redis (for local testing)

### Quick Start

1. **Start infrastructure:**
```bash
# Redis
sudo systemctl start redis-server

# PostgreSQL (via k3s)
sudo kubectl apply -f infrastructure/postgres/
```

2. **Run services locally:**
```bash
# Terminal 1 - Worker
cd services/worker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Terminal 2 - Gateway
cd services/gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

3. **Test the flow:**
```bash
# Submit job
curl -X POST "http://localhost:8000/jobs/submit?job_type=test" \
     -H "Content-Type: application/json" \
     -d '{"duration": 3}'

# Check metrics
curl http://localhost:8001/metrics
```

### Deploy to k3s

1. **Build images:**
```bash
./build-images.sh
```

2. **Import to k3s:**
```bash
docker save gateway:latest | sudo k3s ctr images import -
docker save worker:latest | sudo k3s ctr images import -
```

3. **Deploy:**
```bash
sudo kubectl apply -k infrastructure/
```

4. **Access services:**
```bash
# Add to /etc/hosts
echo "127.0.0.1 gateway.local worker.local" | sudo tee -a /etc/hosts

# Test gateway
curl http://gateway.local/health

# Submit job
curl -X POST "http://gateway.local/jobs/submit?job_type=test" \
     -d '{"duration": 2}'
```

## Failure Injection Demos

### 1. OOM Simulation

Demonstrates worker resource exhaustion:

```bash
# Enable OOM mode
curl -X POST http://localhost:8001/oom/enable

# Submit jobs that leak memory
for i in {1..10}; do
  curl -X POST "http://localhost:8000/jobs/submit?job_type=oom_simulation"
done

# Watch worker memory
watch curl -s http://localhost:8001/oom/status

# Worker will eventually OOMKill in k8s
sudo kubectl get pods -w
```

### 2. Circuit Breaker

Demonstrates fail-fast under queue failures:

```bash
# Stop Redis to trigger failures
sudo systemctl stop redis-server

# Submit jobs - circuit will open after 3 failures
for i in {1..5}; do
  curl -X POST "http://localhost:8000/jobs/submit?job_type=test"
done

# Check circuit state
curl http://localhost:8000/circuit/status
# Output: {"state": "open", ...}

# Restart Redis
sudo systemctl start redis-server

# Circuit will half-open after timeout, then close
```

### 3. Backpressure

Demonstrates queue depth monitoring:

```bash
# Submit many jobs quickly
for i in {1..100}; do
  curl -X POST "http://localhost:8000/jobs/submit?job_type=test" &
done

# Watch queue depth and worker metrics
watch curl -s http://localhost:8001/metrics

# Worker logs will show backpressure warnings
sudo kubectl logs -f deployment/worker
```

## Current Status

**✅ Stage 0 (Foundation): Complete**
- Multi-service distributed architecture
- Gateway → Redis → Worker flow functional
- Circuit breaker implemented
- OOM simulation working
- Backpressure detection active
- Kubernetes manifests ready
- Dockerfiles written

**🚧 Stage 1 (Basic CI/CD): In Progress**
- GitHub Actions workflow to be added
- Automated build + deploy pipeline

## Tech Stack

- **Language**: Python 3.12
- **Framework**: FastAPI + Uvicorn
- **Queue**: Redis
- **Database**: PostgreSQL (SQLAlchemy async)
- **Orchestration**: Kubernetes (k3s)
- **CI/CD**: GitHub Actions (planned)
- **GitOps**: ArgoCD (Stage 5)

## Why This Project Matters

Most CI/CD tutorials show the finished pipeline. This project shows **how pipelines actually evolve**:

1. You start with basic build + deploy
2. Add reliability when things break
3. Add security when compliance asks
4. Add trust when supply chain matters
5. Add enterprise features when scale requires it

Each stage is **git-reviewable** — you can see exactly what changed and why.

Built by [Ibrahim Cisse](https://github.com/ibraheemcisse) as a demonstration of production-grade SRE practices.
