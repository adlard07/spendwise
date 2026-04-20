from fastapi import APIRouter, HTTPException

from src.category import services
from src.models.categories import CreateCategory, UpdateCategory

router = APIRouter(prefix="/category", tags=["Categories"])


@router.post("/add", status_code=201)
def create_category(payload: CreateCategory):
    try:
        result = services.create_category(payload)
        return {"message": "Category created successfully", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create category: {str(e)}"
        )


@router.get("/{category_id}/active")
def get_active_categories(category_id: str):
    try:
        categories = services.get_active_categories(category_id)
        return {"data": categories, "count": len(categories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def get_category(category_id: str):
    try:
        category = services.get_category(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return {"data": category}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{category_id}")
def update_category(category_id: str, payload: UpdateCategory):
    try:
        result = services.update_category(category_id, payload)
        return {"message": "Category updated", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: str):
    try:
        services.delete_category(category_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{category_id}/deactivate")
def deactivate_category(category_id: str):
    try:
        result = services.deactivate_category(category_id)
        return {"message": "Category deactivated", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    category_data = {
        "name": "housing",  # Transportation, Food, Utilities, Healthcare
        "description": "used for home loan, rents, or tax",
        "is_active": True,
    }
