from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/racional_api_dev"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
