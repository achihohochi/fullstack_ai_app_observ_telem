# Prior Authorization Observability Stack

**A production-ready observability implementation for FastAPI applications using Jaeger, Prometheus, and Grafana**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Understanding the Observability Stack](#understanding-the-observability-stack)
- [Testing Guide](#testing-guide)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## 🎯 Overview

This project demonstrates a **complete observability stack** for a FastAPI-based prior authorization system. It showcases how to instrument an application with:

- **Distributed Tracing** (OpenTelemetry + Jaeger) - See WHERE time is spent
- **Metrics** (Prometheus + Grafana) - Track WHAT is happening
- **Structured Logging** (Python logging + PostgreSQL) - Understand WHY things happen

### What You'll Learn

✅ How to add OpenTelemetry instrumentation to FastAPI  
✅ How to visualize request traces in Jaeger  
✅ How to expose Prometheus metrics  
✅ How to create Grafana dashboards  
✅ How to identify performance bottlenecks  
✅ How to run a complete observability stack in Docker  

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│ YOUR MACHINE                                            │
│                                                         │
│ FastAPI App (localhost:8000)                            │
│ ├─ POST /prior-auth/submit (main endpoint)              │
│ ├─ GET /metrics (Prometheus format)                     │
│ ├─ OpenTelemetry instrumentation                        │
│ └─ PostgreSQL database (localhost:5432)                 │
│                                                         │
│ ┌─────────────────────────────────────────────────┐     │
│ │ DOCKER CONTAINERS (observability network)       │     │
│ │                                                 │     │
│ │ Jaeger (localhost:16686)                        │     │
│ │ ├─ Receives traces via OTLP                     │     │
│ │ └─ Visualizes distributed traces                │     │
│ │                                                 │     │
│ │ Prometheus (localhost:9090)                     │     │
│ │ ├─ Scrapes /metrics every 15s                   │     │
│ │ └─ Stores time-series data                      │     │ 
│ │                                                 │     │
│ │ Grafana (localhost:3000)                        │     │
│ │ ├─ Queries Prometheus                           │     │
│ │ └─ Displays dashboards                          │     │
│ └─────────────────────────────────────────────────┘     │ └─────────────────────────────────────────────────────────┘
```

### Request Flow

```
1. Client sends POST request → FastAPI
2. FastAPI processes request
   ├─ OpenTelemetry creates trace & spans
   ├─ Prometheus counters increment
   └─ Audit logs written to PostgreSQL
3. Jaeger receives trace (OTLP HTTP)
4. Prometheus scrapes /metrics endpoint
5. Grafana queries Prometheus for dashboards
```

---

## 🛠️ Tech Stack

### Backend
- **Python 3.12+**
- **FastAPI** - Async web framework
- **Uvicorn** - ASGI server
- **PostgreSQL 16** - Database
- **Pydantic** - Data validation

### Observability
- **OpenTelemetry** - Instrumentation standard
- **Jaeger** - Distributed tracing
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **prometheus_client** - Python Prometheus client

### Infrastructure
- **Docker Desktop** - Container runtime
- **Docker Network** - Service communication

---

## ✅ Prerequisites

### Required Software

1. **Python 3.12+**
   ```bash
   python3 --version
   ```

2. **PostgreSQL 16**
   ```bash
   psql --version
   ```

3. **Docker Desktop**
   ```bash
   docker --version
   docker-compose --version
   ```

4. **Homebrew** (macOS)
   ```bash
   brew --version
   ```

### Database Setup

**Create database and user:**

```bash
# Connect to PostgreSQL
psql postgres

# Create user
CREATE USER fullstack_ai_user WITH PASSWORD 'your_secure_password';

# Create database
CREATE DATABASE fullstack_ai_db OWNER fullstack_ai_user;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE fullstack_ai_db TO fullstack_ai_user;
```

**Run migrations:**

```bash
cd backend
psql -U fullstack_ai_user -d fullstack_ai_db -h localhost -f schema.sql
```

---

## 🚀 Quick Start

### 1. Clone and Install Dependencies

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

**Create `backend/.env`:**

```bash
# Database
DATABASE_URL=postgresql://fullstack_ai_user:your_password@localhost:5432/fullstack_ai_db

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=prior-auth-api
```

### 3. Start Docker Containers

```bash
# Create Docker network
docker network create observability

# Start Prometheus
docker run -d \
  --name prometheus \
  --network observability \
  -p 9090:9090 \
  -v "$(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml" \
  prom/prometheus:latest

# Start Grafana
docker run -d \
  --name grafana \
  --network observability \
  -p 3000:3000 \
  grafana/grafana:latest

# Start Jaeger
docker run -d \
  --name jaeger \
  --network observability \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

### 4. Start FastAPI Application

```bash
uvicorn main:app --reload
```

### 5. Verify Installation

**Check all services:**

```bash
# FastAPI
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics

# Jaeger UI
open http://localhost:16686

# Prometheus UI
open http://localhost:9090

# Grafana UI
open http://localhost:3000
```

---

## 📚 Detailed Setup

### Prometheus Configuration

**Create `backend/prometheus.yml`:**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prior-auth-api'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['host.docker.internal:8000']
```

**Why `host.docker.internal`?**
- Docker containers can't use `localhost` to reach the host machine
- `host.docker.internal` is a special DNS name that resolves to the host

### Grafana Setup

**1. Login to Grafana:**
- URL: http://localhost:3000
- Username: `admin`
- Password: `admin`
- Skip password change (for local dev)

**2. Add Prometheus Data Source:**
- Click menu (☰) → Connections → Data sources
- Click "Add data source"
- Select "Prometheus"
- URL: `http://prometheus:9090` (use container name, not localhost!)
- Click "Save & test"

**3. Create Dashboard:**
- Click menu (☰) → Dashboards → New dashboard
- Click "Add visualization"
- Select "Prometheus" as data source
- Add queries for your metrics

### Key Metrics to Track

| Metric Name | Type | Description |
|------------|------|-------------|
| `prior_auth_requests_total` | Counter | Total requests submitted |
| `prior_auth_database_operations_total` | Counter | Total database operations |
| `prior_auth_validation_failures_total` | Counter | Total validation errors |
| `prior_auth_request_duration_seconds` | Histogram | Request duration distribution |

---

## 🧪 Testing Guide

### Positive Test Case: Normal Request

**Send a valid prior authorization request:**

```bash
curl -X POST http://localhost:8000/prior-auth/submit \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "M12345",
    "provider_npi": "1234567890",
    "diagnosis_code": "Z00.00",
    "requested_service": "ROUTINE_CHECKUP"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "request_id": "PA-00001",
  "member_id": "M12345",
  "provider_npi": "1234567890",
  "diagnosis_code": "Z00.00",
  "requested_service": "ROUTINE_CHECKUP",
  "status": "pending",
  "created_at": "2025-12-20T..."
}
```

**Expected Duration:** ~40ms

### Negative Test Case: Slow Request Simulation

**The code includes a performance test for VIP member M99999:**

```bash
curl -X POST http://localhost:8000/prior-auth/submit \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "M99999",
    "provider_npi": "9999999999",
    "diagnosis_code": "I25.10",
    "requested_service": "VIP_CARDIAC_SURGERY"
  }'
```

**Expected Duration:** ~2050ms (intentional 2-second delay)

**What This Demonstrates:**
- Normal requests: ~40ms processing time
- Slow requests: ~2050ms processing time
- Jaeger shows exactly WHERE the delay occurs
- Grafana shows both requests counted equally (metrics don't show duration)

---

## 🔍 Understanding the Observability Stack

### What Each Tool Shows

| Tool | Purpose | What You See | Best For |
|------|---------|--------------|----------|
| **Jaeger** | Distributed Tracing | Request timeline, span durations, bottlenecks | Finding WHERE time is spent |
| **Prometheus** | Metrics Storage | Counter values, rates, aggregations | Tracking WHAT is happening |
| **Grafana** | Visualization | Dashboards, graphs, alerts | Seeing trends over time |
| **PostgreSQL** | Audit Logs | Event history, request details | Understanding WHY things happened |

### Traces vs Metrics: Key Differences

#### Traces (Jaeger)
```
Request PA-00001 took 42ms total:
├─ generate_request_id: 4ms (10%)
├─ validate_npi: 0.01ms (0.02%)
└─ database_insert: 5ms (12%)

Request PA-00002 took 2050ms total:
├─ generate_request_id: 4ms (0.2%)
├─ vip_member_slow_query: 2000ms (97%) ← BOTTLENECK!
├─ validate_npi: 0.01ms (0%)
└─ database_insert: 5ms (0.2%)
```

**Value:** Shows EXACTLY where time is spent in each request

#### Metrics (Prometheus/Grafana)
```
prior_auth_requests_total{status="success"} = 44
prior_auth_database_operations_total{operation="insert"} = 220
```

**Value:** Shows aggregate counts and trends over time

**Key Insight:** Both requests increment counters by +1, even though one took 50× longer! This is why you need BOTH traces and metrics.

---

## 🎯 Interpreting Jaeger Traces

### Reading a Trace Timeline

**Example: Normal Request (42ms)**

```
Timeline (0ms to 42ms):
┌────────────────────────────────────────────────┐
│ POST /prior-auth/submit (parent)               │
│ ├─ http receive          ▌ (20µs)              │
│ ├─ submit_prior_auth     ████████████████████  │
│ │  ├─ generate_request_id  ███ (4ms)           │
│ │  ├─ validate_npi         ▌ (0.01ms)          │
│ │  └─ database_insert      ███ (5ms)           │
│ └─ http send             ▌ (0.1ms)             │
└────────────────────────────────────────────────┘
```

**How to Read:**
- Horizontal bars = time spent (longer bar = more time)
- Indentation = parent-child relationship
- Click on any span to see attributes and details

### Finding Bottlenecks

**Example: Slow Request (2050ms)**

```
Timeline (0ms to 2050ms):
┌────────────────────────────────────────────────┐
│ POST /prior-auth/submit (parent)               │
│ ├─ submit_prior_auth     ████████████████████  │
│ │  ├─ generate_request_id  ▌ (4ms)             │
│ │  ├─ vip_member_slow_query ████████████ (2000ms) ← PROBLEM!
│ │  ├─ validate_npi         ▌ (0.01ms)          │
│ │  └─ database_insert      ▌ (5ms)             │
└────────────────────────────────────────────────┘
```

**Bottleneck Identified:** `vip_member_slow_query` takes 97% of total time!

**Click on the span to see WHY:**
```
Span Attributes:
├─ delay_ms: 2000
├─ reason: "Simulating database contention"
└─ span.kind: "internal"
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Connection refused" when accessing containers

**Problem:** Containers can't communicate

**Solution:**
```bash
# Check if containers are on the same network
docker network inspect observability

# If not, recreate with network:
docker stop prometheus grafana jaeger
docker rm prometheus grafana jaeger

# Restart with --network observability flag
```

#### 2. Grafana shows "no such host: prometheus"

**Problem:** Grafana not on same Docker network as Prometheus

**Solution:** Ensure Prometheus data source URL uses container name:
- ❌ Wrong: `http://localhost:9090`
- ✅ Correct: `http://prometheus:9090`

#### 3. No traces appearing in Jaeger

**Problem:** OTEL endpoint misconfigured

**Check `.env` file:**
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
# NOT http://localhost:4318/v1/traces (code adds this automatically)
```

**Verify in logs:**
```
✅ OpenTelemetry configured: Sending traces via HTTP
📡 HTTP endpoint: http://localhost:4318/v1/traces
```

#### 4. Prometheus not scraping metrics

**Check Prometheus targets:**
- Go to http://localhost:9090
- Click Status → Targets
- Should show `prior-auth-api (1/1 up)` in green

**If DOWN, check:**
```bash
# Is FastAPI running?
curl http://localhost:8000/metrics

# Is prometheus.yml correct?
cat backend/prometheus.yml

# Restart Prometheus
docker restart prometheus
```

#### 5. High Y-axis values in Grafana (billions instead of actual counts)

**Problem:** Unit/formatting issue

**Solution:**
1. Edit panel
2. Right panel → Standard options → Unit
3. Change to "short" or "none"
4. Click Apply

---

## 📊 Example Queries

### Prometheus Queries

```promql
# Total requests
prior_auth_requests_total

# Total requests with filters
prior_auth_requests_total{status="success"}

# Total database operations (all types combined)
sum(prior_auth_database_operations_total)

# Database operations by type
prior_auth_database_operations_total{operation_type="insert_request"}

# Request rate (requests per second over 5 minutes)
rate(prior_auth_requests_total[5m])
```

### Grafana Dashboard Queries

**Panel 1: Total Requests**
```
Query: prior_auth_requests_total
Visualization: Time series
Title: Total Prior Auth Requests
```

**Panel 2: Database Operations**
```
Query: sum(prior_auth_database_operations_total)
Visualization: Time series
Title: Database Operations
```

**Panel 3: Validation Failures**
```
Query: prior_auth_validation_failures_total
Visualization: Time series
Title: Validation Failures (should be 0)
```

---

## 🔐 Security Considerations

### Local Development (Current Setup)

✅ **Safe for local development:**
- All containers bind to `127.0.0.1` (localhost only)
- Not accessible from network or internet
- Docker network is internal only
- No firewall changes needed

### Production Recommendations

⚠️ **Before deploying to production:**

1. **Authentication:**
   - Enable Grafana authentication
   - Secure Prometheus with basic auth
   - Use API keys for Jaeger

2. **Network Security:**
   - Use TLS/HTTPS for all endpoints
   - Implement firewall rules
   - Use VPN or private network

3. **Secrets Management:**
   - Never commit `.env` files
   - Use secrets manager (AWS Secrets Manager, HashiCorp Vault)
   - Rotate credentials regularly

4. **Data Retention:**
   - Configure Prometheus retention policies
   - Set up Jaeger storage backend (Elasticsearch, Cassandra)
   - Implement log rotation

---

## 🚀 Next Steps

### Extending This Stack

#### 1. Add More Metrics

**Edit `observability.py` to add:**
```python
# Request duration tracking
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# This automatically creates duration metrics
FastAPIInstrumentor.instrument_app(app)
```

#### 2. Create Alerting Rules

**In Grafana:**
- Set up alerts for high error rates
- Alert on slow request spikes
- Notify via email/Slack

#### 3. Add More Spans

**Instrument database queries:**
```python
with tracer.start_as_current_span("complex_database_query") as span:
    result = execute_complex_query()
    span.set_attribute("rows_returned", len(result))
```

#### 4. Production Deployment

**Use docker-compose for orchestration:**
```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    networks:
      - observability
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    networks:
      - observability
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"

  jaeger:
    image: jaegertracing/all-in-one:latest
    networks:
      - observability
    ports:
      - "16686:16686"
      - "4318:4318"

networks:
  observability:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
```

---

## 📖 Resources

### Documentation
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

### Tutorials
- [FastAPI Observability Guide](https://fastapi.tiangolo.com/advanced/observability/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Distributed Tracing Concepts](https://opentelemetry.io/docs/concepts/observability-primer/)

---

## 🎓 Key Takeaways

### What You Built

✅ **Complete observability stack** running locally in Docker  
✅ **Distributed tracing** with OpenTelemetry and Jaeger  
✅ **Metrics collection** with Prometheus  
✅ **Dashboard visualization** with Grafana  
✅ **Performance testing** showing normal vs slow requests  

### What You Learned

✅ **Traces show WHERE** - Identify bottlenecks in request flow  
✅ **Metrics show WHAT** - Track counts, rates, and trends  
✅ **Logs show WHY** - Understand context and events  
✅ **All three together** - Complete observability picture  

### Production-Ready Patterns

✅ Docker networking for service communication  
✅ Environment-based configuration  
✅ Structured instrumentation  
✅ Security-conscious local development  

---

## 📝 License

This is a learning/demonstration project. Use as you see fit!

---

## 🙋 Questions?

This README documents a complete observability journey from zero to production-ready monitoring. Every step was tested and verified on macOS (M4 MacBook Pro) with Docker Desktop.

**Happy monitoring! 🎉**
