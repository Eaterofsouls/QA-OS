from pydantic import BaseModel, ConfigDict, Field
import datetime
class BaseEntity(BaseModel):
    model_config = ConfigDict(frozen=False, extra='forbid')
    id: str
    tenant_id: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
