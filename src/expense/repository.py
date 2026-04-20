from typing import Optional, List, Dict, Any
from src.models.expense import CreateExpense, UpdateExpense
from src.database.dynamo.services import DynamoClient


class ExpenseRepository:
    """Repository for expense CRUD operations."""
    
    def __init__(self):
        self.db = DynamoClient()
    
    def create_expense(self, expense: CreateExpense) -> Dict[str, Any]:
        """Create new expense."""
        data = expense.model_dump(mode='json')
        return self.db.put_item(data)
    
    def get_expense(self, expense_id: str) -> Optional[Dict[str, Any]]:
        """Get expense by ID."""
        return self.db.get_item({"expense_id": expense_id})
    
    def get_expenses( self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all expenses for a user."""
        return self.db.query_by_key("user_id", user_id, limit=limit)
    
    def update_expense( self, expense_id: str, expense: UpdateExpense) -> Dict[str, Any]:
        """Update existing expense."""
        data = expense.model_dump(exclude_unset=True, mode='json')
        return self.db.update_one(
            {"expense_id": expense_id},
            {"$set": data}
        )
    
    def delete_expense(self, expense_id: str) -> None:
        """Delete expense by ID."""
        self.db.delete_one({"expense_id": expense_id})
    
    def get_expenses_by_category( self, user_id: str, category_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get expenses filtered by category."""
        return self.db.query_by_filter(
            {"user_id": user_id, "category_id": category_id},
            limit=limit
        )
    
    def get_recurring_expenses(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all recurring expenses for a user."""
        return self.db.query_by_filter({"user_id": user_id, "is_recurring": True})