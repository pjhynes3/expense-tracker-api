from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from .cache import cache_delete, cache_get, cache_set
from .models import Expense, ExpenseCreate, ExpensePage, ExpenseUpdate
from .storage import ExpenseStorage


class ExpenseService:
    def __init__(self) -> None:
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
    ) -> Expense | None:
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
    ) -> Expense | None:
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
        category: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ExpensePage:
        """
        Return one page of expenses with pagination metadata.
        Do not cache list operations.
        """

        if start_date is not None and end_date is not None and start_date > end_date:
            raise ValueError("start_date must be on or before end_date")

        if (
            min_amount is not None
            and max_amount is not None
            and min_amount > max_amount
        ):
            raise ValueError("min_amount must be less than or equal to max_amount")

        start_at = (
            datetime.combine(start_date, time.min, tzinfo=UTC)
            if start_date is not None
            else None
        )

        end_before = (
            datetime.combine(
                end_date + timedelta(days=1),
                time.min,
                tzinfo=UTC,
            )
            if end_date is not None
            else None
        )

        expenses, total = self.storage.list_expenses(
            user_id=user_id,
            category=category,
            start_at=start_at,
            end_before=end_before,
            min_amount=min_amount,
            max_amount=max_amount,
            page=page,
            page_size=page_size,
        )

        pages = (total + page_size - 1) // page_size

        return ExpensePage(
            items=expenses,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
