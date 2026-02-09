from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers import wallet
from app.exceptions import WalletException, InsufficientFundsError, IdempotencyError

app = FastAPI(
    title="Internal Wallet Service",
    description="A service for managing user wallets, transactions, and ledger operations.",
    version="1.0.0"
)

app.include_router(wallet.router)

@app.exception_handler(WalletException)
async def wallet_exception_handler(request: Request, exc: WalletException):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message},
    )

@app.exception_handler(IdempotencyError)
async def idempotency_exception_handler(request: Request, exc: IdempotencyError):
    return JSONResponse(
        status_code=409,
        content={"detail": exc.message},
    )

@app.get("/")
async def root():
    return {"message": "Wallet Service is running. Access /docs for API documentation."}
