from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from utils.utils import generate_uuid, get_current_timestamp


class CreateTransaction(BaseModel):
    transaction_id: str = Field(default_factory=generate_uuid)
    user_id: str
    amount: float
    title: str
    notes: Optional[str] = None
    transaction_type: Literal["income", "expense", "transfer"] = "expense"
    timestamp: Optional[datetime] = Field(default_factory=get_current_timestamp)
    merchant_id: Optional[str] = None
    category_id: Optional[str] = None
    attachments: Optional[List[str]] = None
    source: Optional[str] = None
    is_duplicate: Optional[bool] = False
    duplicate_of: Optional[str] = None
    created_at: datetime = Field(default_factory=get_current_timestamp)
    updated_at: datetime = Field(default_factory=get_current_timestamp)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UpdateTransaction(BaseModel):
    amount: Optional[float] = None
    transaction_type: Optional[Literal["income", "expense", "transfer"]] = None
    currency: Optional[
        Literal[
            "INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "HKD", "NZD"
        ]
    ] = None
    timestamp: Optional[datetime] = None
    merchant_id: Optional[str] = None
    category_id: Optional[str] = None
    account_id: Optional[str] = None
    notes: Optional[str] = None
    attachments: Optional[List[str]] = None
    source: Optional[str] = None
    is_duplicate: Optional[bool] = None
    duplicate_of: Optional[str] = None
    updated_at: datetime = Field(default_factory=get_current_timestamp)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class RequestTransaction(BaseModel):
    user_id: str
