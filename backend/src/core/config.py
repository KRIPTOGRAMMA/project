from pydantic_settings import BaseSettings
from pydantic import Field

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
    class Config:
        env_file = '.env'
        case_sensitive = False
        populate_by_name = True
        extra = 'ignore'

settings = Settings()