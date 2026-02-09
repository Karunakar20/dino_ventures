from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

class TransactionType(str, Enum):
    TOPUP = "topup"
    PURCHASE = "purchase"
    BONUS = "bonus"
    REFUND = "refund"

class AccountSchema(BaseModel):
    id: int
    name: str
    currency: str
    balance: int
    
    class Config:
        from_attributes = True

class UserSchema(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr]
    
    class Config:
        from_attributes = True

class BalanceResponse(BaseModel):
    user_id: int
    total_balance: int
    accounts: List[AccountSchema]

class TransactionRequest(BaseModel):
    reference_id: str = Field(..., description="Unique ID for idempotency")
    amount: int = Field(..., gt=0, description="Amount in cents/credits")
    description: Optional[str] = None

class TopUpRequest(TransactionRequest):
    user_id: int

class BonusRequest(TransactionRequest):
    user_id: int

class PurchaseRequest(TransactionRequest):
    user_id: int

class TransactionResponse(BaseModel):
    id: int
    reference_id: str
    type: TransactionType
    status: str = "success"
    created_at: datetime
    
    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    detail: str
