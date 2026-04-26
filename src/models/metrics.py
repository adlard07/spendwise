from pydantic import BaseModel


class RequestMetrics(BaseModel):
    user_id: str
    required_fields: list[str] | str = "all"
