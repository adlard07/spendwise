from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from src.expense.services import (create_expense, get_expense, get_expenses, 
                                  update_expense, delete_expense, get_expenses_by_category, 
                                  get_recurring_expenses, get_total_expenses)
from src.models.expense import CreateExpense, UpdateExpense

router = APIRouter(prefix="/expenses", 
                   tags=["expenses", "expense management", "expense operations",])

@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/add", status_code=status.HTTP_201_CREATED)
async def create_expense(expense: CreateExpense):
    """Create new expense."""
    try:
        result = create_expense(expense)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create expense: {str(e)}"
        )


@router.get("/{expense_id}")
async def get_expense(expense_id: str):
    """Get expense by ID."""
    result = get_expense(expense_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    return {"success": True, "data": result}


@router.get("/user/{user_id}")
async def get_user_expenses(
    user_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100)
):
    """Get all expenses for a user."""
    try:
        results = get_expenses(user_id, limit)
        return {
            "success": True,
            "data": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch expenses: {str(e)}"
        )


@router.get("/user/{user_id}/category/{category_id}")
async def get_expenses_by_category(
    user_id: str,
    category_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100)
):
    """Get expenses by category for a user."""
    try:
        results = get_expenses_by_category(user_id, category_id, limit)
        return {
            "success": True,
            "data": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch expenses: {str(e)}"
        )


@router.get("/user/{user_id}/recurring")
async def get_recurring_expenses(user_id: str):
    """Get all recurring expenses for a user."""
    try:
        results = get_recurring_expenses(user_id)
        return {
            "success": True,
            "data": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recurring expenses: {str(e)}"
        )


@router.get("/user/{user_id}/total")
async def get_total_expenses(user_id: str):
    """Calculate total expenses for a user."""
    try:
        total = get_total_expenses(user_id)
        return {
            "success": True,
            "data": {"user_id": user_id, "total_expenses": total}
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate total: {str(e)}"
        )


@router.put("/{expense_id}")
async def update_expense(expense_id: str, update_data: UpdateExpense):
    """Update expense."""
    if not update_data.model_dump(exclude_unset=True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    try:
        result = update_expense(expense_id, update_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update expense: {str(e)}"
        )


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: str):
    """Delete expense."""
    try:
        delete_expense(expense_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete expense: {str(e)}"
        )