from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from database import Base

# 1. ALWAYS PUT THE USER MODEL FIRST
class User(Base):
    __tablename__ = "users"  # <-- Notice this is lowercase "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Relationship back to sessions
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete")


# 2. PUT THE CHAT SESSION MODEL SECOND
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    
    # FIX: Ensure this string points EXACTLY to "users.id" (matching your User tablename)
    user_id = Column(Integer, ForeignKey("users.id")) 
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete")


# 3. PUT THE CHAT MESSAGE MODEL THIRD
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)  
    content = Column(Text)  # (This has your capital 'Text' fix from earlier!)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")