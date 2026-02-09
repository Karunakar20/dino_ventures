from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas import (
    TopUpRequest, BonusRequest, PurchaseRequest, TransactionResponse, 
    BalanceResponse, AccountSchema, TransactionType
)
from app.services.ledger import LedgerService
from app.models import Account, User
from app.exceptions import WalletException, AccountNotFoundError, InsufficientFundsError, IdempotencyError

router = APIRouter(prefix="/wallet", tags=["wallet"])

async def get_system_account(db: AsyncSession, name: str) -> Account:
    """Helper to retrieve a system account by name."""
    result = await db.execute(select(Account).where(Account.name == name))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=500, detail=f"System account '{name}' not found")
    return account

async def get_user_main_account(db: AsyncSession, user_id: int) -> Account:
    """Helper to retrieve the main wallet account for a user."""
    result = await db.execute(select(Account).where(Account.user_id == user_id))
    accounts = result.scalars().all()
    if not accounts:
        raise HTTPException(status_code=404, detail="User wallet not found")
    # In a real scenario, we might have multiple accounts. Returning the first one for now.
    return accounts[0]

@router.post("/topup", response_model=TransactionResponse)
async def top_up(request: TopUpRequest, db: AsyncSession = Depends(get_db)):
    """
    Process a top-up transaction.
    Source: Treasury (System)
    Destination: User Wallet
    """
    service = LedgerService(db)
    
    treasury = await get_system_account(db, "Treasury")
    user_wallet = await get_user_main_account(db, request.user_id)
    
    # Debit User (+), Credit Treasury (-)
    entries = [
        (treasury.id, -request.amount),
        (user_wallet.id, request.amount)
    ]
    
    try:
        tx = await service.process_transaction(
            reference_id=request.reference_id,
            transaction_type=TransactionType.TOPUP,
            description=request.description or "Wallet Top-up",
            entries=entries
        )
        await db.commit()
        return tx
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bonus", response_model=TransactionResponse)
async def bonus(request: BonusRequest, db: AsyncSession = Depends(get_db)):
    """
    Issue a bonus to a user.
    Source: Treasury (System)
    Destination: User Wallet
    """
    service = LedgerService(db)
    treasury = await get_system_account(db, "Treasury")
    user_wallet = await get_user_main_account(db, request.user_id)
    
    entries = [
        (treasury.id, -request.amount),
        (user_wallet.id, request.amount)
    ]
    
    try:
        tx = await service.process_transaction(
            reference_id=request.reference_id,
            transaction_type=TransactionType.BONUS,
            description=request.description or "Bonus Credit",
            entries=entries
        )
        await db.commit()
        return tx
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/spend", response_model=TransactionResponse)
async def spend(request: PurchaseRequest, db: AsyncSession = Depends(get_db)):
    """
    Process a purchase transaction.
    Source: User Wallet
    Destination: Treasury (System)
    """
    service = LedgerService(db)
    treasury = await get_system_account(db, "Treasury")
    user_wallet = await get_user_main_account(db, request.user_id)
    
    entries = [
        (user_wallet.id, -request.amount),
        (treasury.id, request.amount)
    ]
    
    try:
        tx = await service.process_transaction(
            reference_id=request.reference_id,
            transaction_type=TransactionType.PURCHASE,
            description=request.description or "Purchase Item",
            entries=entries
        )
        await db.commit()
        return tx
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}/balance", response_model=BalanceResponse)
async def get_balance(user_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve the total balance and account details for a user."""
    result = await db.execute(select(Account).where(Account.user_id == user_id))
    accounts = result.scalars().all()
    
    total = sum(acc.balance for acc in accounts)
    
    return BalanceResponse(
        user_id=user_id,
        total_balance=total,
        accounts=accounts
    )
