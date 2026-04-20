from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from src.models.transaction import CreateTransaction, UpdateTransaction
from src.transaction.services import (
    create_transaction,
    delete_transaction,
    get_transaction,
    get_transactions_by_category,
    get_user_transactions,
    mark_as_duplicate,
    update_transaction,
)

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
)


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/add", status_code=status.HTTP_201_CREATED)
async def add_transaction(transaction: CreateTransaction):
    """Create new transaction."""
    try:
        result = create_transaction(transaction)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}",
        )


@router.get("/user/{user_id}")
async def fetch_user_transactions(
    user_id: str, limit: Optional[int] = Query(None, ge=1, le=100)
):
    """Get all transactions for a user."""
    try:
        results = get_user_transactions(user_id, limit)
        return {"success": True, "data": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transactions: {str(e)}",
        )


@router.get("/user/{user_id}/category/{category_id}")
async def fetch_transactions_by_category(
    user_id: str,
    category_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100),
):
    """Get transactions by category for a user."""
    try:
        results = get_transactions_by_category(user_id, category_id, limit)
        return {"success": True, "data": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transactions: {str(e)}",
        )


@router.get("/user/{user_id}/{transaction_id}")
async def fetch_transaction(user_id: str, transaction_id: str):
    """Get transaction by full primary key."""
    result = get_transaction(user_id, transaction_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
    return {"success": True, "data": result}


@router.put("/user/{user_id}/{transaction_id}")
async def edit_transaction(
    user_id: str, transaction_id: str, update_data: UpdateTransaction
):
    """Update transaction."""
    if not update_data.model_dump(exclude_unset=True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )
    try:
        result = update_transaction(user_id, transaction_id, update_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update transaction: {str(e)}",
        )


@router.delete(
    "/user/{user_id}/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_transaction(user_id: str, transaction_id: str):
    """Delete transaction."""
    try:
        delete_transaction(user_id, transaction_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete transaction: {str(e)}",
        )


@router.post("/user/{user_id}/{transaction_id}/mark-duplicate")
async def mark_duplicate(
    user_id: str, transaction_id: str, duplicate_of: str = Query(...)
):
    """Mark transaction as duplicate."""
    try:
        result = mark_as_duplicate(user_id, transaction_id, duplicate_of)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark as duplicate: {str(e)}",
        )


if __name__ == "__main__":
    transaction_data = {
        "user_id": "46775c8e-dd7f-4c11-bf0d-15d04e0305b0",
        "amount": 482.00,
        "transaction_type": "expense",
        "merchant_id": "swiggy",
        "category_id": "cat_food_dining",
        "notes": "Dinner order from Swiggy",
        "source": "UPI",
    }
