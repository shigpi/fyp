from backend.core.database import engine, Base
from backend.models.user import User

from sqlalchemy.exc import ProgrammingError

# Drop the users table
try:
    User.__table__.drop(engine)
    print("Users table dropped.")
except ProgrammingError:
    print("Users table did not exist.")

# Recreate tables (optional here as main.py does it, but good for immediate effect)
Base.metadata.create_all(bind=engine)
print("Tables recreated.")
