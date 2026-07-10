from typing import List, Optional
from datetime import datetime, timezone
from .database import SessionLocal
from .db_models import ExpenseRow
import uuid

from .models import Expense, ExpenseCreate, ExpenseUpdate, ExpenseCategory


class ExpenseStorage:
    def _row_to_expense(self, expense_row: ExpenseRow) -> Expense:
        return Expense(
            id=expense_row.id,
            description=expense_row.description,
            amount=expense_row.amount,
            category=ExpenseCategory(expense_row.category),
            created_at=expense_row.created_at,
            updated_at=expense_row.updated_at,
        )
    
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

        expense = self._row_to_expense(expense_row)
        return expense

    def get_expense(self, expense_id: str) -> Optional[Expense]:
        db = SessionLocal()
        expense_row = (
            db.query(ExpenseRow).filter(ExpenseRow.id == expense_id).first()
        )
        if expense_row is None:
            db.close()
            return None
        expense = self._row_to_expense(expense_row)
        db.close()
        return expense

    def update_expense(
        self,
        expense_id: str,
        updates: ExpenseUpdate,
    ) -> Optional[Expense]:
        db = SessionLocal()
        expense_row = (
            db.query(ExpenseRow).filter(ExpenseRow.id==expense_id).first()
        )
        if expense_row is None:
            db.close()
            return None
        if updates.description is not None:
            expense_row.description = updates.description
        if updates.amount is not None:
            expense_row.amount = updates.amount
        if updates.category is not None:
            expense_row.category = updates.category.value

        expense_row.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(expense_row)
        expense = self._row_to_expense(expense_row)
        db.close()
        return expense


    def delete_expense(self, expense_id: str) -> bool:
        db = SessionLocal()
        expense_row = (
            db.query(ExpenseRow).filter(ExpenseRow.id==expense_id).first()
        )
        if expense_row is None:
            db.close()
            return False
        db.delete(expense_row)
        db.commit() # make it official
        db.close()
        return True

    def list_expenses(
        self,
        category: Optional[str] = None,
    ) -> List[Expense]:
        db = SessionLocal()
        
        query = db.query(ExpenseRow)

        if category is not None:
            query = query.filter(ExpenseRow.category == category)

        expense_rows = query.all()

        expenses = [
            self._row_to_expense(row)
            for row in expense_rows
        ]

        db.close()
        return expenses
        