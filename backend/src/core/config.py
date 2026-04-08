from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / '.env'

class Settings(BaseSettings):
    db_url: str = Field(..., alias="DB_URL")
    
    # JWT
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm_key: str = Field(..., alias="JWT_ALGORITHM_KEY")
    
    # App
    environment: str = Field('development', alias="ENVIRONMENT")
    
    # Token expiration
    jwt_expiration_minutes: int = 15
    refresh_token_expiration_days: int = 7

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        extra="ignore"
    )

settings = Settings()