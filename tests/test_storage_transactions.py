from unittest.mock import MagicMock

import pytest

from app.models import ExpenseCategory, ExpenseCreate
from app.storage import ExpenseStorage


def test_create_expense_rolls_back_when_commit_fails(monkeypatch):
    # Arrange: create a fake SessionLocal factory and session.
    mock_session_factory = MagicMock()
    mock_session_context = mock_session_factory.return_value
    mock_db = mock_session_context.__enter__.return_value

    # Force commit() to fail every time it is called.
    mock_db.commit.side_effect = RuntimeError("Simulated database commit failure")

    # Replace the real SessionLocal used by storage.py.
    monkeypatch.setattr(
        "app.storage.SessionLocal",
        mock_session_factory,
    )

    expense_data = ExpenseCreate(
        description="Rollback test expense",
        amount=25.00,
        category=ExpenseCategory.FOOD,
        merchant="Test Merchant",
    )

    storage = ExpenseStorage()

    # Act/Assert: the original commit exception is re-raised.
    with pytest.raises(
        RuntimeError,
        match="Simulated database commit failure",
    ):
        storage.create_expense(
            expense_data=expense_data,
            user_id="test-user-id",
        )

    # Assert: the failed transaction was explicitly rolled back.
    mock_db.commit.assert_called_once_with()
    mock_db.rollback.assert_called_once_with()

    # Assert: execution left the session context manager.
    mock_session_context.__exit__.assert_called_once()
