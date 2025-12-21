import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health():
    print_section("1. HEALTH CHECK")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def submit_valid_requests():
    print_section("2. SUBMITTING VALID PRIOR AUTH REQUESTS")
    
    valid_requests = [
        {"member_id": "M10001", "provider_npi": "1234567890", "diagnosis_code": "E11.9", "requested_service": "MRI_BRAIN"},
        {"member_id": "M10002", "provider_npi": "9876543210", "diagnosis_code": "I10", "requested_service": "CT_CHEST"},
        {"member_id": "M10003", "provider_npi": "5555555555", "diagnosis_code": "J44.0", "requested_service": "XRAY_CHEST"},
        {"member_id": "M10004", "provider_npi": "1111111111", "diagnosis_code": "Z23", "requested_service": "ECHO_CARDIO"},
        {"member_id": "M10005", "provider_npi": "2222222222", "diagnosis_code": "M79.3", "requested_service": "PHYSICAL_THERAPY"},
    ]
    
    for i, req in enumerate(valid_requests, 1):
        print(f"✅ Submitting request {i}/5: Member {req['member_id']}")
        response = requests.post(f"{BASE_URL}/prior-auth/submit", json=req)
        if response.status_code == 201:
            data = response.json()
            print(f"   Created: {data['request_id']} - Status: {data['status']}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
        time.sleep(0.5)

def submit_invalid_requests():
    print_section("3. SUBMITTING INVALID REQUESTS (Testing Validation)")
    
    invalid_requests = [
        {"member_id": "M20001", "provider_npi": "BAD_NPI", "diagnosis_code": "E11", "requested_service": "TEST"},
        {"member_id": "M20002", "provider_npi": "ABCDEFGHIJ", "diagnosis_code": "E11", "requested_service": "TEST"},
        {"member_id": "M20003", "provider_npi": "123", "diagnosis_code": "E11", "requested_service": "TEST"},
    ]
    
    for i, req in enumerate(invalid_requests, 1):
        print(f"❌ Submitting invalid request {i}/3: NPI={req['provider_npi']}")
        response = requests.post(f"{BASE_URL}/prior-auth/submit", json=req)
        if response.status_code != 201:
            print(f"   Expected failure: {response.json()['detail']}")
        time.sleep(0.5)

def trigger_errors():
    print_section("4. TRIGGERING TEST ERRORS (Observability Demo)")
    
    error_types = [
        {"error_type": "validation_error", "description": "Missing field error"},
        {"error_type": "database_timeout", "description": "5 second timeout"},
    ]
    
    for error in error_types:
        print(f"⚠️  Triggering: {error['description']}")
        start = time.time()
        response = requests.post(f"{BASE_URL}/prior-auth/test/errors", json={"error_type": error["error_type"]})
        elapsed = time.time() - start
        print(f"   Status: {response.status_code} (took {elapsed:.2f}s)")
        time.sleep(1)

def list_all_requests():
    print_section("5. LISTING ALL PRIOR AUTH REQUESTS")
    response = requests.get(f"{BASE_URL}/prior-auth/requests")
    requests_data = response.json()
    print(f"Total requests in database: {len(requests_data)}")
    print("\nMost recent 5:")
    for req in requests_data[:5]:
        print(f"  {req['request_id']} | {req['member_id']} | {req['status']} | {req['created_at']}")

def show_summary():
    print_section("6. DEMO COMPLETE - CHECK YOUR OBSERVABILITY!")
    print("""
What to check now:

1. Server Terminal (where uvicorn is running):
   - Look at all the 📥 📝 ✅ ⚠️ logs
   - See timestamps showing when each event occurred

2. Database Audit Trail:
   psql -U fullstack_ai_user -d fullstack_ai_db -h localhost -c "SELECT request_id, event_type, message, timestamp FROM request_logs ORDER BY timestamp DESC LIMIT 20;"

3. All Requests:
   psql -U fullstack_ai_user -d fullstack_ai_db -h localhost -c "SELECT * FROM prior_auth_requests ORDER BY created_at DESC;"

4. API Documentation:
   Open http://localhost:8000/docs

This demonstrates:
✅ Request validation (accepted valid, rejected invalid)
✅ Audit trail (every event logged with timestamp)
✅ Error handling (timeouts, validation errors tracked)
✅ Observability (can trace every request through the system)
""")

if __name__ == "__main__":
    print("\n" + "🏥 " * 20)
    print("PRIOR AUTHORIZATION OBSERVABILITY DEMO")
    print("🏥 " * 20)
    
    try:
        test_health()
        submit_valid_requests()
        submit_invalid_requests()
        trigger_errors()
        list_all_requests()
        show_summary()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API. Is the server running?")
        print("   Run: uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
