from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

url = "postgresql+psycopg://adminxd:pompa@postgres:5432/strange_db";

engine = create_engine(url);
session = sessionmaker(autocommit=False, autoflush=False, bind=engine);

Base = declarative_base();

def get_db():
	db = session();
	try:
		yield db;
	finally:
		db.close();