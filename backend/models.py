from pydantic import BaseModel, Field
from datetime import datetime

class PriorAuthRequest(BaseModel):
    member_id: str = Field(..., min_length=1, max_length=50)
    provider_npi: str = Field(..., min_length=10, max_length=10)
    diagnosis_code: str = Field(..., min_length=1, max_length=20)
    requested_service: str = Field(..., min_length=1, max_length=100)

class PriorAuthResponse(BaseModel):
    id: int
    request_id: str
    member_id: str
    provider_npi: str
    diagnosis_code: str
    requested_service: str
    status: str
    created_at: datetime

class ErrorInjection(BaseModel):
    error_type: str

class HealthCheck(BaseModel):
    status: str
    database: str
    timestamp: datetime
