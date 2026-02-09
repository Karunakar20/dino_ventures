from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/wallet_db"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
