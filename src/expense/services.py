from typing import Optional, List, Dict, Any
from src.models.expense import CreateExpense, UpdateExpense
from src.expense.repository import ExpenseRepository


repository = ExpenseRepository()

def create_expense(self, expense: CreateExpense) -> Dict[str, Any]:
    """Create new expense with validation."""
    return self.repository.create_expense(expense)

def get_expense(self, expense_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve expense by ID."""
    return self.repository.get_expense(expense_id)

def get_expenses(self,user_id: str,limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get all expenses for specific user."""
    return self.repository.get_expenses(user_id, limit)

def update_expense(self,expense_id: str,expense: UpdateExpense) -> Dict[str, Any]:
    """Update expense details."""
    return self.repository.update_expense(expense_id, expense)

def delete_expense(self, expense_id: str) -> None:
    """Delete expense."""
    self.repository.delete_expense(expense_id)

def get_expenses_by_category(self,user_id: str,category_id: str,limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get expenses filtered by category."""
    return self.repository.get_expenses_by_category(user_id, category_id, limit)

def get_recurring_expenses(self, user_id: str) -> List[Dict[str, Any]]:
    """Get all recurring expenses."""
    return self.repository.get_recurring_expenses(user_id)

def get_total_expenses(self, user_id: str) -> float:
    """Calculate total expenses for a user."""
    expenses = self.get_expenses(user_id)
    return sum(expense.get('amount', 0) for expense in expenses)

