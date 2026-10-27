from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://atomize:atomize@localhost:5432/atomize"
    aws_region: str = "us-east-1"
    receipts_bucket_name: str = "atomize-receipts-dev"
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""


settings = Settings()
