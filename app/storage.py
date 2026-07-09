from typing import Dict, List, Optional
from datetime import datetime, timezone
from .database import SessionLocal
from .db_models import ExpenseRow
import uuid

from .models import Expense, ExpenseCreate, ExpenseUpdate, ExpenseCategory


class ExpenseStorage:
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
        db = SessionLocal()
        expense_row = (
            db.query(ExpenseRow).filter(ExpenseRow.id == expense_id).first()
        )
        if expense_row is None:
            db.close()
            return None
        db.close()
        return Expense(
            id = expense_row.id,
            description=expense_row.description,
            amount=expense_row.amount,
            category=ExpenseCategory(expense_row.category),
            created_at=expense_row.created_at,
            updated_at=expense_row.updated_at,
        )

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

        expense = Expense(
            id=expense_row.id,
            description=expense_row.description,
            amount=expense_row.amount,
            category=ExpenseCategory(expense_row.category),
            created_at=expense_row.created_at,
            updated_at=expense_row.updated_at,
        )
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
            Expense(
            id=row.id,
            description=row.description,
            amount=row.amount,
            category=ExpenseCategory(row.category),
            created_at=row.created_at,
            updated_at=row.updated_at,
            )
            for row in expense_rows
        ]

        db.close()
        return expenses
        