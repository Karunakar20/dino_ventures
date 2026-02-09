from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Tuple, Dict
from app.models import Account, Transaction, Posting, TransactionType
from app.exceptions import InsufficientFundsError, AccountNotFoundError, IdempotencyError

class LedgerService:
    """
    Service for handling ledger operations including balance checks and transaction processing.
    Ensures double-entry bookkeeping principles, idempotency, and data consistency.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(self, account_id: int) -> int:
        """
        Retrieves the current balance for a specific account.
        
        Args:
            account_id: The ID of the account to retrieve.
            
        Returns:
            int: The current balance of the account.
            
        Raises:
            AccountNotFoundError: If the account does not exist.
        """
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
        if not account:
            raise AccountNotFoundError(account_id)
        return account.balance

    async def process_transaction(
        self,
        reference_id: str,
        transaction_type: TransactionType,
        description: str,
        entries: List[Tuple[int, int]],
    ) -> Transaction:
        """
        Processes a transaction with double-entry bookkeeping.
        Ensures atomicity, idempotency, and handles concurrency via row locking.

        Args:
            reference_id: Unique identifier for idempotency.
            transaction_type: Type of transaction (e.g., TOPUP, PURCHASE).
            description: Human-readable description of the transaction.
            entries: List of tuples representing (account_id, amount). 
                     Positive amount adds to balance, negative subtracts.
                     Sum of amounts MUST be 0.

        Returns:
            Transaction: The created transaction record.

        Raises:
            ValueError: If entries do not sum to zero.
            IdempotencyError: If a transaction with the same reference_id already exists.
            AccountNotFoundError: If any referenced account does not exist.
            InsufficientFundsError: If an account would go into negative balance (ledger rules).
        """
        
        # 1. Validate Double Entry Rule
        total_amount = sum(amount for _, amount in entries)
        if total_amount != 0:
            raise ValueError(f"Transaction entries do not sum to zero. Sum: {total_amount}")

        # 2. Idempotency Check
        existing_tx_query = select(Transaction).where(Transaction.reference_id == reference_id)
        result = await self.db.execute(existing_tx_query)
        existing_tx = result.scalar_one_or_none()
        if existing_tx:
            raise IdempotencyError(reference_id)

        # 3. Locking & Account Validation
        # Sort account IDs to prevent deadlocks (canonical ordering)
        unique_account_ids = sorted(list(set(acc_id for acc_id, _ in entries)))
        
        # Lock accounts using SELECT ... FOR UPDATE
        query = select(Account).where(Account.id.in_(unique_account_ids)).order_by(Account.id).with_for_update()
        result = await self.db.execute(query)
        accounts = result.scalars().all()
        
        if len(accounts) != len(unique_account_ids):
            found_ids = {acc.id for acc in accounts}
            missing_ids = set(unique_account_ids) - found_ids
            raise AccountNotFoundError(list(missing_ids)[0])
            
        accounts_map: Dict[int, Account] = {acc.id: acc for acc in accounts}

        # 4. Create Transaction Record
        transaction = Transaction(
            reference_id=reference_id,
            type=transaction_type,
            description=description
        )
        self.db.add(transaction)
        await self.db.flush() # Flush to generate transaction ID

        # 5. Create Postings and Update Balances
        for account_id, amount in entries:
            account = accounts_map[account_id]
            
            new_balance = account.balance + amount
            
            # Enforce non-negative balance for standard accounts
            # In a real system, we might have specific account types (e.g., EQUITY, LIABILITY) 
            # that differ in rules, but typically user wallets (ASSETS) cannot go negative.
            # We exempt system accounts like 'Equity' or 'Treasury' from this check if needed,
            # but for safety, we assume 'Treasury' is sufficiently funded or allow it to be negative 
            # if it represents a liability source.
            if new_balance < 0 and account.name not in ["Equity", "Treasury"]:
                raise InsufficientFundsError(account_id)
            
            account.balance = new_balance
            
            posting = Posting(
                transaction_id=transaction.id,
                account_id=account.id,
                amount=amount
            )
            self.db.add(posting)

        return transaction
