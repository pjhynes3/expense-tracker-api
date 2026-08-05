from datetime import date
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Response,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .database import is_database_ready
from .db_models import UserRow
from .expense_service import ExpenseService
from .models import (
    Expense,
    ExpenseCreate,
    ExpensePage,
    ExpenseUpdate,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from .security import create_access_token, decode_access_token
from .user_service import UserService

app = FastAPI(title="Expense Tracker API")

expense_service = ExpenseService()
user_service = UserService()
bearer_scheme = HTTPBearer()


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def readiness_check(response: Response) -> dict[str, str]:
    if not is_database_ready():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not ready"}

    return {"status": "ready"}


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
) -> UserRow:
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


CurrentUser = Annotated[UserRow, Depends(get_current_user)]


@app.get("/me", response_model=UserResponse)
async def read_current_user(current_user: CurrentUser) -> UserResponse:
    return UserResponse(
        id=current_user.id, email=current_user.email, created_at=current_user.created_at
    )


@app.post("/expenses", response_model=Expense, status_code=201)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user: CurrentUser,
) -> Expense:
    try:
        return expense_service.create_expense(
            expense_data,
            current_user.id,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@app.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user_data: UserCreate) -> UserResponse:
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
) -> TokenResponse:
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
    current_user: CurrentUser,
) -> Expense:
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
    current_user: CurrentUser,
) -> Expense:
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
async def delete_expense(expense_id: str, current_user: CurrentUser) -> dict[str, str]:
    deleted = expense_service.delete_expense(
        expense_id,
        current_user.id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted successfully"}


@app.get("/expenses", response_model=ExpensePage)
async def list_expenses(
    current_user: CurrentUser,
    category: Annotated[str | None, Query()] = None,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ExpensePage:
    try:
        return expense_service.list_expenses(
            user_id=current_user.id,
            category=category,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        )
