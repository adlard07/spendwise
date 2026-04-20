from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from utils.utils import generate_uuid, get_current_timestamp


class CreateCategory(BaseModel):
    category_id: str = Field(default_factory=generate_uuid)
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=get_current_timestamp)
    updated_at: datetime = Field(default_factory=get_current_timestamp)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UpdateCategory(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    budget_limit: Optional[float] = None
    is_active: Optional[bool] = None
    updated_at: datetime = Field(default_factory=get_current_timestamp)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
