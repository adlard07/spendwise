from __future__ import annotations

from typing import Any, Literal

from src.database.dynamo.services import DynamoClient

MetricResult = dict[str, Any]
MetricName = Literal[
    "total_spend",
    "avg_daily_spend",
    "largest_spend",
    "top_category",
    "bottom_category",
    "category_spend",
    "estimated_budget",
    "budget_used",
    "total_budget",
]


class Spendings:
    def __init__(self, db: DynamoClient) -> None:
        self.db = db

    def total_spend(self, user_id: str | None = None) -> dict[Any]:
        return {"value": 0.0, "comment": ""}

    def avg_daily_spend(self, user_id: str | None = None) -> dict[Any]:
        return {"value": 0.0, "comment": ""}

    def largest_spend(self, user_id: str | None = None) -> dict[Any]:
        return {"value": 0.0, "comment": ""}


class Category:
    def __init__(self, db: DynamoClient) -> None:
        self.db = db
        self.user_id: str | None = None

    def get_top_category(self, user_id: str | None = None) -> dict[str]:
        return {"value": "", "comment": ""}

    def bottom_category(self, user_id: str | None = None) -> dict[str]:
        return {"value": "", "comment": ""}

    def get_category_spend(
        self,
        category: str,
        user_id: str | None = None,
    ) -> dict[Any]:
        return {"value": 0.0, "comment": ""}


class Budget:
    def __init__(self, db: DynamoClient) -> None:
        self.db = db
        self.user_id: str | None = None

    def total_budget(self, user_id: str | None = None) -> dict[Any]:
        return {"value": 0.0, "comment": ""}

    def budget_used(self, user_id: str | None = None) -> dict[Any]:
        return {"value": 0.0, "comment": ""}

    def estimated_budget(self, user_id: str | None = None) -> dict[Any]:
        return {"value": 0.0, "comment": ""}
