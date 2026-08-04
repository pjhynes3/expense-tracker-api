from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field


class ExpenseCategory(str, Enum):
    FOOD = "food"
    TRANSPORTATION = "transportation"
    RENT = "rent"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    OTHER = "other"


Money = Annotated[
    Decimal,
    Field(max_digits=12, decimal_places=2),
]


class ExpenseCreate(BaseModel):
    description: str
    amount: Money
    category: ExpenseCategory
    merchant: str | None = None


class ExpenseUpdate(BaseModel):
    description: str | None = None
    amount: Money | None = None
    category: ExpenseCategory | None = None
    merchant: str | None = None


class Expense(BaseModel):
    id: str
    description: str
    amount: Money
    category: ExpenseCategory
    merchant: str | None = None
    created_at: datetime
    updated_at: datetime


class ExpensePage(BaseModel):
    items: list[Expense]
    total: int
    page: int
    page_size: int
    pages: int


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):  # what successful login will return
    access_token: str
    token_type: str
