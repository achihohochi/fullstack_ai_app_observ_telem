"""
main.py
-------
FastAPI application for Prior Authorization System with full observability.

This version includes:
- OpenTelemetry distributed tracing (every request tracked)
- Prometheus metrics (counters, histograms, timers)
- Database audit logging
- Automatic FastAPI instrumentation
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import Response
from typing import List
import logging
from datetime import datetime
import time

from models import PriorAuthRequest, PriorAuthResponse, ErrorInjection, HealthCheck
from database import execute_query, get_db_connection

# Import observability functions
from observability import (
    setup_tracing,              # Configures OpenTelemetry
    get_tracer,                 # For creating custom spans
    metrics_endpoint,           # Exposes /metrics for Prometheus
    record_request,             # Records request success/failure count
    record_validation_failure,  # Tracks validation error types
    record_database_operation,  # Counts database queries
    RequestTimer                # Measures endpoint latency
)

# Configure structured logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(title="Prior Auth API", version="1.0.0")

# ✅ OBSERVABILITY SETUP: Auto-instrument FastAPI to trace all requests
setup_tracing(app)

# Get tracer for creating custom spans (manual instrumentation)
tracer = get_tracer(__name__)


def get_next_request_id():
    """
    Generate next request ID based on database count.
    
    Why: Ensures unique, sequential request IDs (PA-00001, PA-00002, etc.)
    """
    query = "SELECT COUNT(*) as count FROM prior_auth_requests"
    result = execute_query(query, fetch=True)
    count = result[0]['count']
    return f"PA-{count + 1:05d}"


def log_event(request_id: str, event_type: str, message: str):
    """
    Log an event to the request_logs audit trail table.
    
    Why: Creates permanent record of what happened and when
    Used for: Compliance, debugging, analytics
    """
    try:
        query = "INSERT INTO request_logs (request_id, event_type, message) VALUES (%s, %s, %s)"
        execute_query(query, (request_id, event_type, message), fetch=False)
        logger.info(f"📝 Logged: {request_id} - {event_type}")
        

        # ✅ PROMETHEUS CALL #2: Record database operation
        # Record metric: database write operation
        record_database_operation("insert_log")
    except Exception as e:
        logger.error(f"Failed to log event: {e}")


@app.get("/")
async def root():
    """
    Root endpoint - confirms API is running.
    
    Observability: Records success metric for monitoring uptime
    """
    record_request("success", "/")
    return {"message": "Prior Authorization API", "status": "running"}


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint - verifies database connectivity.
    
    Observability: 
    - Measures response time with RequestTimer
    - Records success/failure metrics
    Used by: Load balancers, monitoring systems
    """
    with RequestTimer("/health"):
        try:
            conn = get_db_connection()
            conn.close()
            record_request("success", "/health")
            return {"status": "healthy", "database": "connected", "timestamp": datetime.now()}
        except:
            record_request("error", "/health")
            return {"status": "unhealthy", "database": "disconnected", "timestamp": datetime.now()}


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus format (scraped by Grafana Cloud)
    Exposes: Request counts, error rates, latency, database operation counts
    """
    return metrics_endpoint()


@app.post("/prior-auth/submit", response_model=PriorAuthResponse, status_code=201)
async def submit_prior_auth(request: PriorAuthRequest):
    """
    Submit a new prior authorization request.
    
    Observability:
    - Main span: "submit_prior_auth" (entire request)
    - Child span: "validate_npi" (validation step)
    - Child span: "database_insert" (database write)
    - Metrics: success/failure counts, validation failure types
    - Logs: Full audit trail in request_logs table
    
    Returns: PriorAuthResponse with generated request_id and status
    """
    
    # Create a trace start span #1 for the entire request
    # This lets us see timing breakdown in Grafana
    with tracer.start_as_current_span("submit_prior_auth") as span:
        # Generate unique request ID
        request_id = get_next_request_id()
        
# ⏱️ PERFORMANCE TEST: Simulate slow processing for VIP member - added RCL testing
        # This demonstrates how observability helps identify bottlenecks
        if request.member_id == "M99999":
            with tracer.start_as_current_span("vip_member_slow_query") as slow_span:
                import time
                slow_span.set_attribute("delay_ms", 2000)
                slow_span.set_attribute("reason", "Simulating database contention")
                logger.warning(f"⚠️  VIP member {request.member_id} - simulating 2s delay")
                time.sleep(2)  # 2000ms delay to simulate slow database query
                logger.info(f"✅ Delay complete for {request_id}")



        # Add attributes to the span (visible in Grafana trace view)
        span.set_attribute("request.id", request_id)
        span.set_attribute("request.member_id", request.member_id)
        span.set_attribute("request.provider_npi", request.provider_npi)
        
        # Log receipt
        logger.info(f"📥 Received request {request_id} from provider {request.provider_npi}")
        log_event(request_id, "REQUEST_RECEIVED", f"Submitted by provider NPI {request.provider_npi}")
        
        # ─────────────────────────────────────────────────────────
        # VALIDATION STEP (separate span to measure timing) - trace start nested span #2 inside span #1
        # ─────────────────────────────────────────────────────────
        with tracer.start_as_current_span("validate_npi"):
            # Business rule: NPI must be exactly 10 digits
            if not request.provider_npi.isdigit() or len(request.provider_npi) != 10:
                logger.warning(f"Invalid NPI format: {request.provider_npi}")
                log_event(request_id, "VALIDATION_FAILED", f"Invalid NPI format: {request.provider_npi}")
                
                
                # ✅ PROMETHEUS CALL #4: Record validation failure
                # Record metrics for monitoring
                record_validation_failure("invalid_npi_format")
                record_request("validation_error", "/prior-auth/submit")
                
                # Return HTTP 400 Bad Request
                raise HTTPException(400, "Provider NPI must be exactly 10 digits")
        
        # Add this trace to see how long it takes to generate request id:
        with tracer.start_as_current_span("generate_request_id"):
                request_id = get_next_request_id() 


        # Validation passed
        log_event(request_id, "VALIDATION_PASSED", "All required fields validated")
        
        # ─────────────────────────────────────────────────────────
        # DATABASE INSERT (separate span to measure DB performance) - - trace start span #3 inside span #1
        # ─────────────────────────────────────────────────────────
        with tracer.start_as_current_span("database_insert"):
            query = """INSERT INTO prior_auth_requests 
                       (request_id, member_id, provider_npi, diagnosis_code, requested_service, status)
                       VALUES (%s, %s, %s, %s, %s, 'pending')
                       RETURNING id, request_id, member_id, provider_npi, diagnosis_code, 
                                 requested_service, status, created_at"""
            
            result = execute_query(
                query, 
                (request_id, request.member_id, request.provider_npi, 
                 request.diagnosis_code, request.requested_service), 
                fetch=True
            )
            
            # ✅ PROMETHEUS CALL #3: Record database insert
            # Record database operation metric
            record_database_operation("insert_request")
        
        # Log success events
        log_event(request_id, "SAVED_TO_DATABASE", f"Request saved for member {request.member_id}")
        log_event(request_id, "STATUS_PENDING", "Awaiting review")
        
        logger.info(f"✅ Created {request_id}")
        
        # # ✅ PROMETHEUS CALL #1: Record successful request
        # Record success metric
        record_request("success", "/prior-auth/submit")
        
        # Return the created request
        return PriorAuthResponse(**result[0])


@app.get("/prior-auth/requests", response_model=List[PriorAuthResponse])
async def list_requests():
    """
    List all prior authorization requests.
    
    Observability:
    - Measures query duration with RequestTimer
    - Records database operation count
    - Tracks endpoint success rate
    """
    with RequestTimer("/prior-auth/requests"):
        query = "SELECT * FROM prior_auth_requests ORDER BY created_at DESC LIMIT 100"
        results = execute_query(query, fetch=True)
        
        # Record metrics
        record_database_operation("select_requests")
        record_request("success", "/prior-auth/requests")
        
        return [PriorAuthResponse(**row) for row in results]


@app.get("/prior-auth/requests/{request_id}/logs")
async def get_request_logs(request_id: str):
    """
    Get audit trail for a specific request.
    
    Shows: All events that happened to this request (received, validated, saved, etc.)
    Why: For debugging, compliance, customer support
    """
    query = "SELECT * FROM request_logs WHERE request_id = %s ORDER BY timestamp"
    logs = execute_query(query, (request_id,), fetch=True)
    
    # Record database operation
    record_database_operation("select_logs")
    
    return {"request_id": request_id, "events": logs}


@app.post("/prior-auth/test/errors")
async def trigger_error(error: ErrorInjection):
    """
    Trigger intentional test errors for observability demonstration.
    
    Why: Shows how errors appear in traces, metrics, and logs
    Used for: Demos, testing monitoring/alerting
    
    Error types:
    - database_timeout: Simulates slow database (5 second delay)
    - validation_error: Simulates missing required field
    """
    error_id = f"ERROR-{int(time.time())}"
    logger.warning(f"⚠️  Triggering {error.error_type}")
    log_event(error_id, "ERROR_TEST_STARTED", f"Testing {error.error_type}")
    
    if error.error_type == "database_timeout":
        # Simulate slow database query
        log_event(error_id, "DATABASE_SLOW", "Simulating 5 second timeout")
        time.sleep(5)  # Intentional delay
        log_event(error_id, "DATABASE_TIMEOUT", "Query exceeded timeout threshold")
        
        # Record error metrics
        record_request("timeout_error", "/prior-auth/test/errors")
        
        # Return HTTP 503 Service Unavailable
        raise HTTPException(503, "Database timeout")
        
    elif error.error_type == "validation_error":
        # Simulate validation failure
        log_event(error_id, "VALIDATION_ERROR", "Missing required field")
        
        # Record error metrics
        record_request("validation_error", "/prior-auth/test/errors")
        
        # Return HTTP 400 Bad Request
        raise HTTPException(400, "Validation failed")
    
    return {"error_triggered": error.error_type}
