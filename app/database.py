from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = 'postgresql://patrick:password123@localhost:5432/expense_tracker'

engine = create_engine(DATABASE_URL)

# Create a configured "SessionLocal" class
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    )

Base = declarative_base()