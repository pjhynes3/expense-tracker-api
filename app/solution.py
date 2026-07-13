from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional

from .models import Expense, ExpenseCreate, ExpenseUpdate, ExpenseCategory
from .expense_service import ExpenseService
from .database import Base, engine
from . import db_models

# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API")

expense_service = ExpenseService()


@app.post("/expenses", response_model=Expense)
async def create_expense(expense_data: ExpenseCreate):
    return expense_service.create_expense(expense_data)

@app.get("/expenses/{expense_id}", response_model=Expense)
async def get_expense(expense_id: str):
    expense = expense_service.get_expense(expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.put("/expenses/{expense_id}", response_model=Expense)
async def update_expense(
    expense_id: str,
    updates: ExpenseUpdate,
):
    try:
        updated_expense = expense_service.update_expense(expense_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if updated_expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return updated_expense


@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    deleted = expense_service.delete_expense(expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Document deleted successfully"}


@app.get("/expenses", response_model=List[Expense])
async def list_expenses(
    category: Optional[str] = Query(None),
):
    return expense_service.list_expenses(category)