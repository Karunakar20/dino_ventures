import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User, Account, Transaction, Posting, TransactionType
from app.config import settings

async def seed():
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(User).limit(1))
        if result.scalar():
            print("Database already seeded.")
            return

        print("Seeding database...")

        # 1. Create System User
        system_user = User(username="system", email="system@dinoventures.com")
        session.add(system_user)
        
        # 2. Create Normal Users
        alice = User(username="alice", email="alice@example.com")
        bob = User(username="bob", email="bob@example.com")
        session.add(alice)
        session.add(bob)
        
        await session.flush()

        # 3. Create Accounts
        # Equity Account (Source of all funds)
        equity_account = Account(user_id=system_user.id, name="Equity", currency="GOLD")
        
        # Treasury Account (Store of funds for the app)
        treasury_account = Account(user_id=system_user.id, name="Treasury", currency="GOLD")
        
        # User Wallets
        alice_wallet = Account(user_id=alice.id, name="Alice's Wallet", currency="GOLD")
        bob_wallet = Account(user_id=bob.id, name="Bob's Wallet", currency="GOLD")
        
        session.add_all([equity_account, treasury_account, alice_wallet, bob_wallet])
        await session.flush()

        # 4. Initial Funding Transaction (Equity -> Treasury)
        # 1 Billion Gold Coins
        genesis_tx = Transaction(
            reference_id="genesis_001",
            type=TransactionType.TOPUP,
            description="Initial Capital Injection"
        )
        session.add(genesis_tx)
        await session.flush()

        # Treasury (Asset) increases with Debit (Positive if we stick to signed balance) 
        # But here we are just adding/subtracting amounts directly.
        # Treasury +1B, Equity -1B.
        
        p1 = Posting(transaction_id=genesis_tx.id, account_id=treasury_account.id, amount=1_000_000_000)
        p2 = Posting(transaction_id=genesis_tx.id, account_id=equity_account.id, amount=-1_000_000_000)
        session.add_all([p1, p2])
        
        treasury_account.balance += 1_000_000_000
        equity_account.balance -= 1_000_000_000

        # 5. Fund Users (Treasury -> User)
        # Give Alice 100, Bob 50
        
        # Alice Tx
        tx_alice = Transaction(
            reference_id="seed_alice_001",
            type=TransactionType.BONUS,
            description="Welcome Bonus for Alice"
        )
        session.add(tx_alice)
        await session.flush()
        
        p_alice_cr = Posting(transaction_id=tx_alice.id, account_id=treasury_account.id, amount=-100)
        p_alice_dr = Posting(transaction_id=tx_alice.id, account_id=alice_wallet.id, amount=100)
        session.add_all([p_alice_cr, p_alice_dr])
        
        treasury_account.balance -= 100
        alice_wallet.balance += 100

        # Bob Tx
        tx_bob = Transaction(
            reference_id="seed_bob_001",
            type=TransactionType.BONUS,
            description="Welcome Bonus for Bob"
        )
        session.add(tx_bob)
        await session.flush()
        
        p_bob_cr = Posting(transaction_id=tx_bob.id, account_id=treasury_account.id, amount=-50)
        p_bob_dr = Posting(transaction_id=tx_bob.id, account_id=bob_wallet.id, amount=50)
        session.add_all([p_bob_cr, p_bob_dr])
        
        treasury_account.balance -= 50
        bob_wallet.balance += 50
        
        await session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed())
