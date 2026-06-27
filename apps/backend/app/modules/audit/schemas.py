from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int | None = None
    actor_email: str | None = None
    actor_role: str | None = None
    method: str
    path: str
    action: str
    status_code: int
    request_id: str | None = None
    created_at: datetime
