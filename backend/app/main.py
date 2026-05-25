from fastapi import FastAPI

from .config import (
    FIRST_MODULE_ID,
    FIRST_MODULE_NAME,
    PRODUCT_FULL_NAME,
    PRODUCT_NAME,
    SUPPORTED_AFFECTED_SERVICES,
)
from .models import HealthResponse, ModuleMetadata, ModulesResponse
from .scan import router as scan_router

app = FastAPI(title="TRACE Backend")
app.include_router(scan_router)


def get_module_metadata() -> ModuleMetadata:
    return ModuleMetadata(
        id=FIRST_MODULE_ID,
        name=FIRST_MODULE_NAME,
        status="phase-2-foundation",
        description=(
            "Diagnoses Microsoft 365 access failures using identity, licensing, "
            "sign-in, Conditional Access, and device compliance evidence."
        ),
        supported_affected_services=list(SUPPORTED_AFFECTED_SERVICES),
    )


@app.get("/api/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(status="ok", product=PRODUCT_NAME, module_count=1)


@app.get("/api/modules", response_model=ModulesResponse)
def get_modules() -> ModulesResponse:
    return ModulesResponse(
        product=PRODUCT_NAME,
        product_full_name=PRODUCT_FULL_NAME,
        modules=[get_module_metadata()],
    )
