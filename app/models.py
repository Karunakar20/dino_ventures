from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class TransactionType(str, enum.Enum):
    TOPUP = "topup"
    PURCHASE = "purchase"
    BONUS = "bonus"
    REFUND = "refund"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    accounts = relationship("Account", back_populates="user")

class Account(Base):
    """
    Represents a financial account (wallet) within the system.
    System accounts (e.g., Treasury) may have a null user_id.
    """
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) 
    name = Column(String, nullable=False) 
    currency = Column(String, default="CREDIT", nullable=False)
    balance = Column(BigInteger, default=0, nullable=False) 
    version = Column(Integer, default=0, nullable=False) # Optimistic locking
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="accounts")
    postings = relationship("Posting", back_populates="account")

class Transaction(Base):
    """
    Represents a logical transaction group consisting of multiple postings.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(String, unique=True, index=True, nullable=False) # Idempotency key
    type = Column(SQLEnum(TransactionType), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    postings = relationship("Posting", back_populates="transaction")

class Posting(Base):
    """
    Represents a single entry in a double-entry bookkeeping transaction.
    The sum of amounts for all postings in a transaction must be zero.
    """
    __tablename__ = "postings"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(BigInteger, nullable=False) # Positive adds to balance, negative subtracts.
    
    transaction = relationship("Transaction", back_populates="postings")
    account = relationship("Account", back_populates="postings")
