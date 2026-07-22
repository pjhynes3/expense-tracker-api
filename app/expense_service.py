from typing import List, Optional

from .models import Expense, ExpenseCreate, ExpenseUpdate
from .storage import ExpenseStorage
from .cache import cache_get, cache_set, cache_delete


class ExpenseService:
    def __init__(self):
        self.storage = ExpenseStorage()

    def create_expense(
            self, 
            expense_data: ExpenseCreate,
            user_id: str,
        ) -> Expense:
        """
        Create expense with business validation.
        Business rule:
            amount must be greater than 0
        """
        if expense_data.amount <= 0:
            raise ValueError("Amount must be greater than 0.00")
        return self.storage.create_expense(
            expense_data, 
            user_id,
        )

    def get_expense(
            self, 
            expense_id: str,
            user_id: str,
        ) -> Optional[Expense]:
        """
        Get an expense owned by the authenticated user
        using cache-aside pattern.
        """
        cache_key = f"expense:{user_id}:{expense_id}"
        expense = cache_get(cache_key)
        if expense is None:
            expense = self.storage.get_expense(expense_id, user_id)
            if expense is not None:
                cache_set(cache_key, expense)
        return expense

    def update_expense(
        self,
        expense_id: str,
        updates: ExpenseUpdate,
        user_id: str,
    ) -> Optional[Expense]:
        """
        Update an expense with owned by the authenticated user.
        Business rule:
            if amount is provided, it must be greater than 0.
        """
        if updates.amount is not None and updates.amount <= 0:
            raise ValueError("Amount must be greater than 0")
        
        updated_expense = self.storage.update_expense(
            expense_id, 
            updates,
            user_id,
        )
        
        if updated_expense is not None:
            cache_key = f"expense:{user_id}:{expense_id}"
            cache_delete(cache_key)
        return updated_expense

    def delete_expense(
            self, 
            expense_id: str,
            user_id: str,
        ) -> bool:
        """
        Delete an expense owned by authenticated user and remove its cached copy.
        """
        deleted = self.storage.delete_expense(
            expense_id,
            user_id,
        )
        if deleted:
            cache_key = f"expense:{user_id}:{expense_id}"
            cache_delete(cache_key)
        return deleted

    def list_expenses(
        self,
        user_id: str,
        category: Optional[str] = None,
    ) -> List[Expense]:
        """
        List expenses with optional category filtering.
        Do not cache list operations.
        """
        return self.storage.list_expenses(
            user_id,
            category,
        )