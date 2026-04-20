from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List
from utils.utils import generate_uuid, get_current_timestamp


class CreateExpense(BaseModel):
    expense_id: str = Field(default_factory=generate_uuid)
    user_id: str
    amount: float
    description: str
    category_id: Optional[str] = None
    merchant_id: Optional[str] = None
    payment_method: Optional[str] = None
    date: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    tags: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    is_recurring: Optional[bool] = False
    recurring_frequency: Optional[str] = None
    created_at: datetime = Field(default_factory=get_current_timestamp)
    updated_at: datetime = Field(default_factory=get_current_timestamp)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UpdateExpense(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    merchant_id: Optional[str] = None
    payment_method: Optional[str] = None
    date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    is_recurring: Optional[bool] = None
    recurring_frequency: Optional[str] = None
    updated_at: datetime = Field(default_factory=get_current_timestamp)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}