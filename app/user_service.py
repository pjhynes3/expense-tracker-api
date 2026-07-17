from .models import UserCreate, UserResponse
from .storage import UserStorage
from .security import hash_password

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