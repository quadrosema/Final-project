from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import DATABASE_URL

engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True)
