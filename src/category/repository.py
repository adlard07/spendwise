import os
from typing import Any, Dict, List, Optional

from boto3.dynamodb.conditions import Attr

from src.database.dynamo.initialize import DynamoClient
from src.models.categories import CreateCategory, UpdateCategory


class CategoryRepository:
    def __init__(self):
        self.db = DynamoClient()
        self.table_name = os.getenv("CATEGORIES_TABLE", "expense-tracker-categories")
        self.PK = "user_id"
        self.SK = "category_id"

    def create_category(self, category_data: CreateCategory) -> Dict[str, Any]:
        """Create new category."""
        data = category_data.model_dump(mode="json")
        return self.db.put_item(
            table_name=self.table_name,
            item=data,
            condition="attribute_not_exists(category_id)",
        )

    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get category by full primary key."""
        return self.db.get_item(
            table_name=self.table_name,
            key={self.PK: category_id},
        )

    def get_user_categories(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all categories for a user."""
        return self.db.query_by_key(
            table_name=self.table_name,
            pk_name=self.PK,
            pk_value=user_id,
            limit=limit,  # type: ignore lmfao boto3
        )

    def get_active_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get only active categories for a user."""
        return self.db.query_by_filter(
            table_name=self.table_name,
            pk_name=self.PK,
            pk_value=user_id,
            filter_expression=Attr("is_active").eq(True),
        )

    def update_category(
        self, category_id: str, update_data: UpdateCategory
    ) -> Dict[str, Any]:
        """Update existing category."""
        updates = update_data.model_dump(exclude_unset=True, mode="json")
        return self.db.update_one(
            table_name=self.table_name,
            key={self.PK: category_id},
            updates=updates,
        )

    def delete_category(self, category_id: str) -> None:
        """Delete category by full primary key."""
        self.db.delete_one(
            table_name=self.table_name,
            key={self.PK: category_id},
        )
