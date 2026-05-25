from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    product: str
    module_count: int


class ModuleMetadata(BaseModel):
    id: str
    name: str
    status: str
    description: str
    supported_affected_services: List[str]


class ModulesResponse(BaseModel):
    product: str
    product_full_name: str
    modules: List[ModuleMetadata]


class ScanRequest(BaseModel):
    user_principal_name: str
    affected_service: str
    scenario: str
    use_sample_data: bool = True


class ScanInput(BaseModel):
    user_principal_name: str
    affected_service: str


class IdentitySnapshot(BaseModel):
    user_exists: bool
    account_enabled: bool
    user_type: str
    display_name: Optional[str] = None


class LicenseSnapshot(BaseModel):
    has_relevant_license: bool
    assigned_skus: List[str] = Field(default_factory=list)


class SignInEvent(BaseModel):
    createdDateTime: Optional[str] = None
    status: str
    failureReason: Optional[str] = None
    resourceDisplayName: Optional[str] = None
    clientAppUsed: Optional[str] = None
    conditionalAccessStatus: Optional[str] = None
    deviceDetail: Optional[Dict[str, Any]] = None


class SignInSnapshot(BaseModel):
    available: bool
    recent_events: List[SignInEvent] = Field(default_factory=list)


class ConditionalAccessPolicy(BaseModel):
    displayName: str
    result: str
    grantControls: List[str] = Field(default_factory=list)


class ConditionalAccessSnapshot(BaseModel):
    details_available: bool
    missing_reason: Optional[str] = None
    policies: List[ConditionalAccessPolicy] = Field(default_factory=list)


class DeviceSnapshot(BaseModel):
    evidence_available: bool
    device_id: Optional[str] = None
    display_name: Optional[str] = None
    compliance_state: Optional[str] = None
    last_check_in: Optional[str] = None


class CollectorErrorDetail(BaseModel):
    code: str
    message: str
    scenario: Optional[str] = None
    known_scenarios: List[str] = Field(default_factory=list)


class CollectorErrorResult(BaseModel):
    status: str
    module: str
    error: CollectorErrorDetail


class CollectorResult(BaseModel):
    scenario_id: str
    module: str
    input: ScanInput
    identity: IdentitySnapshot
    licenses: LicenseSnapshot
    signin_logs: SignInSnapshot
    conditional_access: ConditionalAccessSnapshot
    device: DeviceSnapshot
