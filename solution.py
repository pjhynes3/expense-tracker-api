from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional

from .models import Expense, ExpenseCreate, ExpenseUpdate, ExpenseCategory
from .expense_service import ExpenseService


app = FastAPI(title="Expense Tracker API")

expense_service = ExpenseService()


@app.post("/expenses", response_model=Expense)
async def create_expense(expense_data: ExpenseCreate):
    raise HTTPException(status_code=501, detail="Not implemented")


@app.get("/expenses/{expense_id}", response_model=Expense)
async def get_expense(expense_id: str):
    raise HTTPException(status_code=501, detail="Not implemented")


@app.put("/expenses/{expense_id}", response_model=Expense)
async def update_expense(
    expense_id: str,
    updates: ExpenseUpdate,
):
    raise HTTPException(status_code=501, detail="Not implemented")


@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    raise HTTPException(status_code=501, detail="Not implemented")


@app.get("/expenses", response_model=List[Expense])
async def list_expenses(
    category: Optional[str] = Query(None),
):
    raise HTTPException(status_code=501, detail="Not implemented")