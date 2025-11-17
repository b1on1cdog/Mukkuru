# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' SQLite database
This module should NOT import other Mukkuru modules.\n
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()
engine = None
SessionLocal = None

def init_database(db_path: str):
    """Initialize the database engine at runtime."""
    global engine, SessionLocal
    engine = create_engine(f"sqlite:///{db_path}", echo=False, pool_size=10, max_overflow=20, future=True)
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
