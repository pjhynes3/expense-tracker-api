from typing import Dict, List, Optional
from datetime import datetime, timezone
from .database import SessionLocal
from .db_models import ExpenseRow
import uuid

from .models import Expense, ExpenseCreate, ExpenseUpdate, ExpenseCategory


class ExpenseStorage:
    def __init__(self):
        self._expenses: Dict[str, Expense] = {} # key -> expense:{expense_id} val -> Expense

    def create_expense(self, expense_data: ExpenseCreate) -> Expense:
        now = datetime.now(timezone.utc)
        expense_row = ExpenseRow(
            id = str(uuid.uuid4()),
            description=expense_data.description,
            amount = expense_data.amount,
            category = expense_data.category.value,
            created_at=now,
            updated_at=now,
        )
        
        db = SessionLocal()
        db.add(expense_row)
        db.commit()
        db.refresh(expense_row)
        db.close()

        return Expense(
            id=expense_row.id,
            description=expense_row.description,
            amount=expense_row.amount,
            category=ExpenseCategory(expense_row.category),
            created_at=expense_row.created_at,
            updated_at=expense_row.updated_at,
        )

    def get_expense(self, expense_id: str) -> Optional[Expense]:
        return self._expenses.get(expense_id)

    def update_expense(
        self,
        expense_id: str,
        updates: ExpenseUpdate,
    ) -> Optional[Expense]:
        expense = self._expenses.get(expense_id)        
        if expense is None:
            return None
        if updates.amount is not None:
            expense.amount = updates.amount
        if updates.category is not None:
            expense.category = updates.category
        if updates.description is not None:
            expense.description = updates.description
        expense.updated_at = datetime.now(timezone.utc)
        return expense


    def delete_expense(self, expense_id: str) -> bool:
        expense = self._expenses.get(expense_id)
        if expense is None:
            return False
        del self._expenses[expense_id]
        return True

    def list_expenses(
        self,
        category: Optional[str] = None,
    ) -> List[Expense]:
        expenses = list(self._expenses.values())
        
        if category is not None:
            expenses = [
                expense
                for expense in expenses
                if expense.category == category
            ]
        return expenses