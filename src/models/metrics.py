from typing import Literal

from pydantic import BaseModel


class RequestMetrics(BaseModel):
    user_id: str
    required_fields: list[str] | Literal["all"] = "all"
