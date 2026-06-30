from typing import Dict, List, Optional
from datetime import datetime, timezone
import uuid

from .models import Expense, ExpenseCreate, ExpenseUpdate


class ExpenseStorage:
    def __init__(self):
        self._expenses: Dict[str, Expense] = {} # key -> expense:{expense_id} val -> Expense

    def create_expense(self, expense_data: ExpenseCreate) -> Expense:
        now = datetime.now(timezone.utc)
        expense = Expense(
            id=str(uuid.uuid4()),
            description=expense_data.description,
            amount=expense_data.amount,
            category=expense_data.category,
            created_at=now,
            updated_at=now
        )
        self._expenses[expense.id] = expense
        return expense

    def get_expense(self, expense_id: str) -> Optional[Expense]:
        raise NotImplementedError("TODO: Implement get_expense")

    def update_expense(
        self,
        expense_id: str,
        updates: ExpenseUpdate,
    ) -> Optional[Expense]:
        raise NotImplementedError("TODO: Implement update_expense")

    def delete_expense(self, expense_id: str) -> bool:
        raise NotImplementedError("TODO: Implement delete_expense")

    def list_expenses(
        self,
        category: Optional[str] = None,
    ) -> List[Expense]:
        raise NotImplementedError("TODO: Implement list_expenses")