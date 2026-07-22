from fastapi import (
    FastAPI, 
    HTTPException, 
    Query, 
    status,
    Depends,
    )
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional

from .models import (
    Expense, 
    ExpenseCreate, 
    ExpenseUpdate, 
    ExpenseCategory, 
    UserCreate, 
    UserResponse, 
    UserLogin,
    TokenResponse,
)

from .security import create_access_token, decode_access_token
from .expense_service import ExpenseService
from .user_service import UserService
from . import db_models

app = FastAPI(title="Expense Tracker API")

expense_service = ExpenseService()
user_service = UserService()
bearer_scheme = HTTPBearer()

def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials
    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = user_service.get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@app.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user=Depends(get_current_user)
):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at
    )

@app.post("/expenses", response_model=Expense, status_code=201)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user=Depends(get_current_user)):
    return expense_service.create_expense(
        expense_data, 
        current_user.id,
        )

@app.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user_data: UserCreate):
    try:
        return user_service.register_user(user_data)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

@app.post(
        "/login",
        response_model=TokenResponse,
        status_code=status.HTTP_200_OK,
)
async def login(
    login_data: UserLogin,
):
    user = user_service.authenticate_user(login_data)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    access_token = create_access_token(user.id)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )

@app.get("/expenses/{expense_id}", response_model=Expense)
async def get_expense(
    expense_id: str,
    current_user=Depends(get_current_user)):
    expense = expense_service.get_expense(
        expense_id, 
        current_user.id,
    )
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.put("/expenses/{expense_id}", response_model=Expense)
async def update_expense(
    expense_id: str,
    updates: ExpenseUpdate,
    current_user=Depends(get_current_user)
):
    try:
        updated_expense = expense_service.update_expense(
            expense_id, 
            updates,
            current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if updated_expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return updated_expense


@app.delete("/expenses/{expense_id}")
async def delete_expense(
    expense_id: str,
    current_user=Depends(get_current_user)):
    deleted = expense_service.delete_expense(
        expense_id,
        current_user.id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted successfully"}


@app.get("/expenses", response_model=List[Expense])
async def list_expenses(
    current_user=Depends(get_current_user),
    category: Optional[str] = Query(None)
):
    return expense_service.list_expenses(
        current_user.id,
        category,
    )