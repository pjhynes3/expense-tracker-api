import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]
