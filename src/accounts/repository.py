from typing import Optional, Dict, Any
from src.database.dynamo.services import DatabaseServices

class AccountsRespository:
    """Repository for user accounts."""

    def __init__(self):
        self.db_service = DatabaseServices()

    def get_user_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a user by user ID."""
        return self.db_service.get_item(
            key={"user_id": user_id},
            table_name=self.db_service.users_table
        )

    def create_accounts(self, user_id: str) -> Dict[str, Any]:
        """Create a new accounts."""
        return self.db_service.create_accounts(
            user_id=user_id,

        )