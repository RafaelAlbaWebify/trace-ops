from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BackendValidationError(Exception):
    code: str
    message: str
    details: List[Dict[str, Any]] = field(default_factory=list)
    scenario: Optional[str] = None
    category: str = "validation"

    def to_dict(self) -> Dict[str, Any]:
        error: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "category": self.category,
        }
        if self.scenario is not None:
            error["scenario"] = self.scenario
        if self.details:
            error["details"] = self.details
        return {"status": "error", "error": error}


def validation_error(
    code: str,
    message: str,
    *,
    scenario: Optional[str] = None,
    details: Optional[List[Dict[str, Any]]] = None,
    category: str = "validation",
) -> BackendValidationError:
    return BackendValidationError(
        code=code,
        message=message,
        scenario=scenario,
        details=details or [],
        category=category,
    )
