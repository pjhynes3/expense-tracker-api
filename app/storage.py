from typing import List, Optional
from datetime import datetime, timezone
from .database import SessionLocal
from .db_models import ExpenseRow, UserRow
import uuid

from .models import Expense, ExpenseCreate, ExpenseUpdate, ExpenseCategory, UserCreate, UserResponse


class ExpenseStorage:
    def _row_to_expense(self, expense_row: ExpenseRow) -> Expense:
        return Expense(
            id=expense_row.id,
            description=expense_row.description,
            amount=expense_row.amount,
            category=ExpenseCategory(expense_row.category),
            merchant=expense_row.merchant,
            created_at=expense_row.created_at,
            updated_at=expense_row.updated_at,
        )
    
    def create_expense(
            self, 
            expense_data: ExpenseCreate,
            user_id: str,
        ) -> Expense:
        now = datetime.now(timezone.utc)
        expense_row = ExpenseRow(
            id = str(uuid.uuid4()),
            user_id=user_id,
            description=expense_data.description,
            amount = expense_data.amount,
            category = expense_data.category.value,
            merchant = expense_data.merchant,
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

    def get_expense(
            self, 
            expense_id: str,
            user_id: str,) -> Optional[Expense]:
        db = SessionLocal()
        expense_row = (
            db.query(ExpenseRow)
            .filter(
                ExpenseRow.id == expense_id,
                ExpenseRow.user_id == user_id,
            )
            .first()
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
        if updates.merchant is not None:
            expense_row.merchant = updates.merchant

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
        user_id: str,
        category: Optional[str] = None,
    ) -> List[Expense]:
        db = SessionLocal()
        
        query = (
            db.query(ExpenseRow)
            .filter(ExpenseRow.user_id == user_id)
        )

        if category is not None:
            query = query.filter(ExpenseRow.category == category)

        expense_rows = query.all()

        expenses = [
            self._row_to_expense(row)
            for row in expense_rows
        ]

        db.close()
        return expenses
        

class UserStorage():
    def create_user(
            self,
            email: str,
            hashed_password: str,
    ) -> UserResponse:

        now = datetime.now(timezone.utc)
        user_row = UserRow(
            id = str(uuid.uuid4()),
            email = email,
            hashed_password = hashed_password,
            created_at = now
        )

        db = SessionLocal()
        db.add(user_row)
        db.commit()
        db.refresh(user_row)

        user = UserResponse(
            id=user_row.id,
            email=user_row.email,
            created_at=user_row.created_at,
        )

        db.close()
        return user
    
    def get_user_by_email(self, email: str) -> Optional[UserRow]:
        db = SessionLocal()

        user_row = (
            db.query(UserRow).filter(UserRow.email == email).first()
        )

        db.close()
        return user_row
    
    def get_user_by_id(self, user_id: str) -> Optional[UserRow]:
        db = SessionLocal()

        user_row = (
            db.query(UserRow)
            .filter(UserRow.id == user_id)
            .first()
        )

        db.close()
        return user_row