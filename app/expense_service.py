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

    def get_expense(self, expense_id: str) -> Optional[Expense]:
        """
        Get expense with cache-aside pattern.
        """
        # cache-aside: get it from cache if possible, if not grab from db but populate cache
        expense = cache_get(f"expense:{expense_id}")
        if expense is None:
            expense = self.storage.get_expense(expense_id)
            if expense is not None:
                cache_set(f"expense:{expense_id}", expense)
        return expense

    def update_expense(
        self,
        expense_id: str,
        updates: ExpenseUpdate,
    ) -> Optional[Expense]:
        """
        Update expense with validation.
        Business rule:
            if amount is provided, it must be greater than 0
        Consider cache invalidation.
        """
        if updates.amount is not None and updates.amount <= 0:
            raise ValueError("Amount must be greater than 0")
        
        updated_expense = self.storage.update_expense(expense_id, updates)
        
        if updated_expense is not None:
            cache_delete(f"expense:{expense_id}")
        return updated_expense

    def delete_expense(self, expense_id: str) -> bool:
        """
        Delete expense with cache cleanup.
        """

        deleted = self.storage.delete_expense(expense_id)
        if deleted:
            cache_delete(f"expense:{expense_id}")
        return deleted

    def list_expenses(
        self,
        category: Optional[str] = None,
    ) -> List[Expense]:
        """
        List expenses with optional category filtering.
        Do not cache list operations.
        """
        return self.storage.list_expenses(category)