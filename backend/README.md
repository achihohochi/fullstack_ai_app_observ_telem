# Prior Authorization System - Gather, Instrument and Observability

A production-quality healthcare prior authorization API built with FastAPI, PostgreSQL, and full observability stack.

## 🏥 What This System Does

This is a **prior authorization request system** for healthcare providers (like any US based insurance payor (BSC,UH,Ant,etc). When a doctor needs to perform an expensive procedure or prescribe medication, they must get approval from the insurance company first. This system:

- ✅ Accepts prior authorization requests from providers
- ✅ Validates the request data (2-layer validation)
- ✅ Stores requests in PostgreSQL database
- ✅ Creates complete audit trail (every event logged)
- ✅ Tracks request status (pending, approved, denied)
- ✅ Provides observability (traces, metrics, logs)

## 🏗️ Architecture
```
Provider System → FastAPI Backend → PostgreSQL Database
                       ↓
                  Observability
                  (Logs, Traces, Metrics)
```

### Tech Stack

- **Backend:** Python 3.9, FastAPI, Uvicorn
- **Database:** PostgreSQL 16
- **Validation:** Pydantic
- **Observability:** OpenTelemetry, Prometheus, Grafana Cloud
- **Testing:** pytest, requests library

### Database Schema

**Table 1: prior_auth_requests**
- Main record of each prior authorization request
- Fields: request_id, member_id, provider_npi, diagnosis_code, requested_service, status, created_at

**Table 2: request_logs**
- Audit trail of every event that happens to a request
- Fields: request_id, event_type, message, timestamp

## 🚀 Getting Started

### Prerequisites
```bash
# Check you have these installed:
python3 --version   # Need 3.9+
psql --version      # Need PostgreSQL 16+
```

### Installation

1. **Clone the repository**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up database**
```bash
# Connect to PostgreSQL
psql -U fullstack_ai_user -d fullstack_ai_db -h localhost

# Create tables (copy-paste into psql):
CREATE TABLE prior_auth_requests (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50) UNIQUE NOT NULL,
    member_id VARCHAR(50) NOT NULL,
    provider_npi VARCHAR(10) NOT NULL,
    diagnosis_code VARCHAR(20) NOT NULL,
    requested_service VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE request_logs (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

5. **Configure environment**
```bash
# Create .env file with your database credentials
DATABASE_URL=postgresql://fullstack_ai_user:your_password@localhost:5432/fullstack_ai_db
ENV=development
```

6. **Start the server**
```bash
uvicorn main:app --reload
```

Server runs at: http://localhost:8000

## 📚 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint (API status) |
| GET | `/health` | Health check (database connectivity) |
| POST | `/prior-auth/submit` | Submit new prior auth request |
| GET | `/prior-auth/requests` | List all requests |
| GET | `/prior-auth/requests/{id}` | Get specific request |
| GET | `/prior-auth/requests/{id}/logs` | Get audit trail for request |
| POST | `/prior-auth/test/errors` | Trigger test errors (for observability demo) |

### Interactive Documentation

Open in browser: http://localhost:8000/docs

This shows all endpoints with "Try it out" buttons!

## 🧪 Testing

### Manual Testing

**1. Health check:**
```bash
curl http://localhost:8000/health
```

**2. Submit a valid request:**
```bash
curl -X POST http://localhost:8000/prior-auth/submit \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "M12345",
    "provider_npi": "1234567890",
    "diagnosis_code": "E11.9",
    "requested_service": "MRI_BRAIN"
  }'
```

**3. Test validation failure:**
```bash
curl -X POST http://localhost:8000/prior-auth/submit \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "M12345",
    "provider_npi": "INVALID_NPI",
    "diagnosis_code": "E11.9",
    "requested_service": "TEST"
  }'
```

**4. Trigger test error (5-second timeout):**
```bash
curl -X POST http://localhost:8000/prior-auth/test/errors \
  -H "Content-Type: application/json" \
  -d '{"error_type": "database_timeout"}'
```

### Automated Testing

Run the demo script that submits 10 requests (mix of success/failures):
```bash
python demo_multiple_requests.py
```

## 🔍 Observability

### Viewing Logs

**Server logs** (where uvicorn is running):
- 📥 = Request received
- 📝 = Event logged to database
- ✅ = Success
- ⚠️ = Test error triggered

### Database Audit Trail

**View all events for a specific request:**
```sql
SELECT * FROM request_logs 
WHERE request_id = 'PA-00001' 
ORDER BY timestamp;
```

**View all requests:**
```sql
SELECT * FROM prior_auth_requests 
ORDER BY created_at DESC;
```

**Count success vs failures:**
```sql
SELECT 
  COUNT(CASE WHEN event_type = 'STATUS_PENDING' THEN 1 END) as successful,
  COUNT(CASE WHEN event_type = 'VALIDATION_FAILED' THEN 1 END) as failed
FROM request_logs;
```

## 📊 Request Flow
```
1. Provider submits request
   ↓
2. FastAPI receives → Log: REQUEST_RECEIVED
   ↓
3. Validate NPI format
   ↓
4. Log: VALIDATION_PASSED or VALIDATION_FAILED
   ↓
5. If valid: Save to database → Log: SAVED_TO_DATABASE
   ↓
6. Set status to pending → Log: STATUS_PENDING
   ↓
7. Return response to provider
```

## 🛡️ Two-Layer Validation

**Layer 1: Pydantic (happens first)**
- Checks field length (NPI must be 10 chars)
- Checks required fields present
- Returns HTTP 422 if fails

**Layer 2: Business Logic (in code)**
- Checks NPI contains only digits
- Custom validation rules
- Returns HTTP 400 if fails

## 🐛 Common Issues

**Issue:** `ModuleNotFoundError: No module named 'fastapi'`
**Solution:** Activate virtual environment: `source venv/bin/activate`

**Issue:** `Database connection failed`
**Solution:** Check PostgreSQL is running: `brew services list`

**Issue:** `Port 8000 already in use`
**Solution:** Kill existing process: `lsof -ti:8000 | xargs kill -9`

## 📈 Example Use Cases

### Use Case 1: Track Request Status
```sql
-- Find all pending requests
SELECT * FROM prior_auth_requests WHERE status = 'pending';

-- See what happened to request PA-00001
SELECT * FROM request_logs WHERE request_id = 'PA-00001';
```

### Use Case 2: Identify Failed Validations
```sql
-- Find all validation failures
SELECT request_id, message, timestamp 
FROM request_logs 
WHERE event_type = 'VALIDATION_FAILED'
ORDER BY timestamp DESC;
```

### Use Case 3: Measure Performance
```sql
-- Calculate average time from received to saved
SELECT AVG(
  EXTRACT(EPOCH FROM (
    saved.timestamp - received.timestamp
  ))
) as avg_seconds
FROM request_logs received
JOIN request_logs saved ON received.request_id = saved.request_id
WHERE received.event_type = 'REQUEST_RECEIVED'
  AND saved.event_type = 'SAVED_TO_DATABASE';
```

## 🔮 Future Enhancements

- [ ] Add OpenTelemetry distributed tracing
- [ ] Create Grafana dashboards
- [ ] Build Next.js frontend (provider portal)
- [ ] Add approval workflow
- [ ] Implement status notifications
- [ ] Add authentication/authorization
- [ ] Deploy to cloud (AWS/GCP/Azure)

## 📝 License

MIT License

## 👤 Author - RCL

Built as a testing/training/sandbox project for healthcare observability systems.

---

**Last Updated:** December 18, 2024
