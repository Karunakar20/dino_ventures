class WalletException(Exception):
    pass

class InsufficientFundsError(WalletException):
    def __init__(self, account_id: int):
        self.message = f"Insufficient funds in account {account_id}"
        super().__init__(self.message)

class AccountNotFoundError(WalletException):
    def __init__(self, account_id: int):
        self.message = f"Account {account_id} not found"
        super().__init__(self.message)

class IdempotencyError(WalletException):
    def __init__(self, reference_id: str):
        self.message = f"Transaction with reference_id '{reference_id}' already exists"
        super().__init__(self.message)

class DraglockDetectedError(WalletException):
     pass
