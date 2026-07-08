from sqlalchemy import Column, String, Float, DateTime, Text
from .database import Base


class ExpenseRow(Base):
    __tablename__ = "expenses"
    id = Column(String, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True),nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
