from dataclasses import dataclass
from typing import Optional
import time


@dataclass
class ServiceResult:
    """Data class for service check results"""

    name: str
    status: str
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    details: Optional[str] = None  # Add this field
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "status": self.status,
            "response_time": self.response_time,
            "error_message": self.error_message,
            "details": self.details,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceResult":
        """Create ServiceResult from dictionary"""
        return cls(
            name=data.get("name", ""),
            status=data.get("status", "unknown"),
            response_time=data.get("response_time"),
            error_message=data.get("error_message"),
            details=data.get("details"),
            timestamp=data.get("timestamp"),
        )
