from typing import Any, Dict, List, Optional

from src.models.transaction import CreateTransaction, UpdateTransaction
from src.transaction.repository import TransactionRepository

transaction_repository = TransactionRepository()


def create_transaction(transaction_data: CreateTransaction) -> Dict[str, Any]:
    """Create new transaction with validation."""
    return transaction_repository.create_transaction(transaction_data)


def get_transaction(user_id: str, transaction_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve transaction by full primary key."""
    return transaction_repository.get_transaction(user_id, transaction_id)


def get_user_transactions(
    user_id: str, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get all transactions for specific user."""
    return transaction_repository.get_user_transactions(user_id, limit)


def update_transaction(
    user_id: str, transaction_id: str, update_data: UpdateTransaction
) -> Dict[str, Any]:
    """Update transaction details."""
    return transaction_repository.update_transaction(
        user_id, transaction_id, update_data
    )


def delete_transaction(user_id: str, transaction_id: str) -> None:
    """Delete transaction."""
    transaction_repository.delete_transaction(user_id, transaction_id)


def get_transactions_by_category(
    user_id: str, category_id: str, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get transactions filtered by category."""
    return transaction_repository.get_transactions_by_category(
        user_id, category_id, limit
    )


def mark_as_duplicate(
    user_id: str, transaction_id: str, duplicate_of: str
) -> Dict[str, Any]:
    """Mark transaction as duplicate of another."""
    update_data = UpdateTransaction(is_duplicate=True, duplicate_of=duplicate_of)
    return update_transaction(user_id, transaction_id, update_data)
