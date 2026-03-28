from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # DB_HOST: str
    # DB_USER: str
    # DB_PASSWORD: str
    # DB_NAME: str    
    ACCESS_TOKEN_SECRET_KEY: str
    REFRESH_TOKEN_SECRET_KEY: str
    ALGORITHM: str
    DB_URL: str
    GROQ_API_KEY: Optional[str] = None

    # @property
    # def DATABASE_URL(self) -> str:
    #     return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"

    @property
    def DATABASE_URL(self) -> str:
        return self.DB_URL 

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()