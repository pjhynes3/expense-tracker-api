from typing import List, Optional

from .models import Expense, ExpenseCreate, ExpenseUpdate
from .storage import ExpenseStorage
from .cache import cache_get, cache_set, cache_delete


class ExpenseService:
    def __init__(self):
        self.storage = ExpenseStorage()

    def create_expense(self, expense_data: ExpenseCreate) -> Expense:
        """
        Create expense with business validation.
        Business rule:
            amount must be greater than 0
        """
        raise NotImplementedError("TODO: Implement create_expense")

    def get_expense(self, expense_id: str) -> Optional[Expense]:
        """
        Get expense with cache-aside pattern.
        """
        raise NotImplementedError("TODO: Implement get_expense")

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
        raise NotImplementedError("TODO: Implement update_expense")

    def delete_expense(self, expense_id: str) -> bool:
        """
        Delete expense with cache cleanup.
        """
        raise NotImplementedError("TODO: Implement delete_expense")

    def list_expenses(
        self,
        category: Optional[str] = None,
    ) -> List[Expense]:
        """
        List expenses with optional category filtering.
        Do not cache list operations.
        """
        raise NotImplementedError("TODO: Implement list_expenses")