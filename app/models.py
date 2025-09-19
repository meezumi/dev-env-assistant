
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

class ServiceStatus(Enum):
    UP = "online"
    DOWN = "offline"
    UNHEALTHY = "unhealthy"
    TIMEOUT = "timeout"
    ERROR = "error"


class ServiceType(Enum):
    PORT = "port"
    HTTP = "http"
    TCP = "tcp"


@dataclass
class ServiceResult:
    name: str
    type: str
    host: str = "localhost"
    port: Optional[int] = None
    url: Optional[str] = None
    status: str = "unknown"
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    last_checked: datetime = None
    additional_info: Dict[str, Any] = None

    def __post_init__(self):
        if self.last_checked is None:
            self.last_checked = datetime.now()
        if self.additional_info is None:
            self.additional_info = {}
