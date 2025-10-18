from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
DB_URL=os.getenv('DB_URL','postgresql+psycopg://asiar:change_me@db:5432/asiar')
engine=create_engine(DB_URL)
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
Base=declarative_base()
