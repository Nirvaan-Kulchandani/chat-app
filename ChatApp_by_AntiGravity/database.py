from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./chat.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, index=True)
    sender = Column(String)  # 'user', 'ai', 'human'
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String, index=True) # To group chats if needed, or just global for now
    type = Column(String) # 'text'

def init_db():
    Base.metadata.create_all(bind=engine)
