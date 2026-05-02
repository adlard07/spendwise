from typing import Any, Dict, List, Optional

from boto3.dynamodb.conditions import Attr, Key

from src.database.dynamo.initialize import DynamoClient
from src.models.transaction import CreateTransaction, UpdateTransaction


class TransactionRepository:
    def __init__(self):
        self.db = DynamoClient()
        self.PK = "user_id"
        self.SK = "transaction_id"
        self.table_name = "expense-tracker-transactions"

    def create_transaction(self, transaction_data: CreateTransaction) -> Dict[str, Any]:
        """Create new transaction."""
        data = transaction_data.model_dump(mode="json")
        return self.db.put_item(
            table_name=self.table_name,
            item=data,
            condition="attribute_not_exists(transaction_id)",
        )

    def get_transaction(
        self, user_id: str, transaction_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get transaction by full primary key (self.PK + self.SK)."""
        return self.db.get_item(
            table_name=self.table_name,
            key={self.PK: user_id, self.SK: transaction_id},
        )

    def get_user_transactions(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all transactions for a user."""
        return self.db.query_by_key(
            table_name=self.table_name,
            pk_name=self.PK,
            pk_value=user_id,
            scan_forward=False,
            limit=limit,
        )

    def update_transaction(
        self, user_id: str, transaction_id: str, update_data: UpdateTransaction
    ) -> Dict[str, Any]:
        """Update existing transaction."""
        updates = update_data.model_dump(exclude_unset=True, mode="json")
        return self.db.update_one(
            table_name=self.table_name,
            key={self.PK: user_id, self.SK: transaction_id},
            updates=updates,
        )

    def delete_transaction(self, user_id: str, transaction_id: str) -> None:
        """Delete transaction by full primary key."""
        self.db.delete_one(
            table_name=self.table_name,
            key={self.PK: user_id, self.SK: transaction_id},
        )

    def get_transactions_by_category(
        self, user_id: str, category_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        return self.db.query_by_filter(
            table_name=self.table_name,
            pk_name=self.PK,
            pk_value=user_id,
            filter_expression=Attr("category_id").eq(category_id),
            scan_forward=False,
            limit=limit,
        )

    def get_duplicate_transactions(self, user_id: str) -> List[Dict[str, Any]]:
        return self.db.query_by_filter(
            table_name=self.table_name,
            pk_name=self.PK,
            pk_value=user_id,
            filter_expression=Attr("is_duplicate").eq(True),
        )
