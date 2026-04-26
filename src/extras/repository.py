from __future__ import annotations

from typing import Any, Literal

from src.database.dynamo.services import DynamoClient
from src.extras.metrics import Budget, Category, MetricName, MetricResult, Spendings


class ExtrasRepository:
    def __init__(self, db: DynamoClient | None = None) -> None:
        self.db = db or DynamoClient()
        self.spends = Spendings(self.db)
        self.categories = Category(self.db)
        self.budget = Budget(self.db)

        self.metrics_handlers = {
            "total_spend": self.spends.total_spend,
            "avg_daily_spend": self.spends.avg_daily_spend,
            "largest_expense": self.spends.largest_spend,
            "top_category": self.categories.get_top_category,
            "bottom_category": self.categories.bottom_category,
            "estimated_budget": self.budget.estimated_budget,
            "budget_used": self.budget.budget_used,
            "total_budget": self.budget.total_budget,
        }

    def get_metrics(
        self,
        required: list[MetricName] | Literal["all"] = "all",
        user_id: str | None = None,
    ) -> list[MetricResult]:
        if required == "all":
            selected = list(self.metrics_handlers.keys())
        else:
            invalid = [name for name in required if name not in self.metrics_handlers]
            if invalid:
                raise ValueError(f"Unknown metrics requested: {invalid}")
            selected = list(required)

        return [{name: self.metrics_handlers[name]()} for name in selected]
