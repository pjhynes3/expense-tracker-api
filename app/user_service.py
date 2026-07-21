from .models import UserCreate, UserResponse, UserLogin
from .storage import UserStorage
from .security import hash_password, verify_password


class UserService:
    def __init__(self):
        self.storage = UserStorage()

    def register_user(
            self, 
            user_data:UserCreate,
        ) -> UserResponse:
        # Check whether the email already exists
        existing_user = self.storage.get_user_by_email(user_data.email)
        if existing_user is not None:
            raise ValueError("Email is already registered")
        
        hashed_password = hash_password(user_data.password)

        return self.storage.create_user(
            email=user_data.email,
            hashed_password=hashed_password,
        )
    
    def authenticate_user(
            self,
            login_data: UserLogin,
            ):
        # Retrieve user -> check whether user exists -> Verify submitted password against stored hash -> Return authenticated user
        user = self.storage.get_user_by_email(login_data.email)

        if user is None:
            return None
        
        if not verify_password(
            login_data.password,
            user.hashed_password,
        ):
            return None
        
        return user
    
    def get_user_by_id(self, user_id: str):
        return self.storage.get_user_by_id(user_id)