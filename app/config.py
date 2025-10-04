from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"  # Ignoruj dodatkowe zmienne środowiskowe
    )
    
    database_url: str = "postgresql://postgres:postgres@db:5432/app_db"


settings = Settings()
