from typing import Any, Dict, List, Optional

from src.category.repository import CategoryRepository
from src.models.categories import CreateCategory, UpdateCategory

category_repository = CategoryRepository()


def create_category(category_data: CreateCategory) -> Dict[str, Any]:
    """Create new category with validation."""
    return category_repository.create_category(category_data)


def get_category(category_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve category by full primary key."""
    return category_repository.get_category(category_id)


def get_user_categories(
    user_id: str, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get all categories for a user."""
    return category_repository.get_user_categories(user_id, limit)


def get_active_categories(user_id: str) -> List[Dict[str, Any]]:
    """Get only active categories for a user."""
    return category_repository.get_active_categories(user_id)


def update_category(category_id: str, update_data: UpdateCategory) -> Dict[str, Any]:
    """Update category details."""
    return category_repository.update_category(category_id, update_data)


def delete_category(category_id: str) -> None:
    """Delete category."""
    category_repository.delete_category(category_id)


def deactivate_category(category_id: str) -> Dict[str, Any]:
    """Soft-delete by deactivating a category."""
    update_data = UpdateCategory(is_active=False)
    return update_category(category_id, update_data)
