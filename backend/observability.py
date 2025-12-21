"""
observability.py - Using HTTP exporter for better compatibility
"""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

from dotenv import load_dotenv
load_dotenv()

raw = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
print("OTEL raw headers length:", len(raw))
print("OTEL raw headers startswith:", raw[:25])  # safe; doesn't reveal token


SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "prior-auth-api")
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
OTEL_HEADERS_RAW = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")

requests_total = Counter('prior_auth_requests_total', 'Total number of prior auth requests', ['status', 'endpoint'])
request_duration = Histogram('prior_auth_request_duration_seconds', 'Request duration in seconds', ['endpoint'])
validation_failures = Counter('prior_auth_validation_failures_total', 'Total validation failures', ['failure_type'])
database_operations = Counter('prior_auth_database_operations_total', 'Total database operations', ['operation_type'])


def setup_tracing(app):
    """Set up OpenTelemetry using HTTP exporter (more reliable than gRPC)."""
    
    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ENV", "development")
    })
    
    tracer_provider = TracerProvider(resource=resource)
    
    if OTEL_ENDPOINT:
        headers_dict = {}
        if OTEL_HEADERS_RAW:
            headers_str = OTEL_HEADERS_RAW.strip('"').strip("'")
            for header_pair in headers_str.split(","):
                header_pair = header_pair.strip()
                if "=" in header_pair:
                    key, value = header_pair.split("=", 1)
                    headers_dict[key.strip()] = value.strip()
        
        # Use HTTP endpoint (add /v1/traces to the base URL)
        http_endpoint = OTEL_ENDPOINT.rstrip('/') + '/v1/traces'
        
        print(f"🔑 Using headers: {list(headers_dict.keys())}")
        print(f"📡 HTTP endpoint: {http_endpoint}")
        
        otlp_exporter = OTLPSpanExporter(
            endpoint=http_endpoint,
            headers=headers_dict
        )
        
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        print(f"✅ OpenTelemetry configured: Sending traces via HTTP")
    else:
        print("⚠️  OTEL_ENDPOINT not set")
    
    trace.set_tracer_provider(tracer_provider)
    FastAPIInstrumentor.instrument_app(app)
    print("✅ OpenTelemetry tracing enabled")


def get_tracer(name: str):
    return trace.get_tracer(name)

def metrics_endpoint():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

def record_request(status: str, endpoint: str):
    requests_total.labels(status=status, endpoint=endpoint).inc()

def record_validation_failure(failure_type: str):
    validation_failures.labels(failure_type=failure_type).inc()

def record_database_operation(operation_type: str):
    database_operations.labels(operation_type=operation_type).inc()

class RequestTimer:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        duration = time.time() - self.start_time
        request_duration.labels(endpoint=self.endpoint).observe(duration)
