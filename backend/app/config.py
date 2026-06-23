from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "RSYSLOG Manager API"
    jwt_secret: str = Field(default="CHANGE_ME")
    jwt_algorithm: str = "HS256"
    jwt_expiration_seconds: int = 3600
    admin_username: str = Field(default="admin")
    admin_password: str = Field(default="admin123")

    model_config = {"env_file": ".env"}


settings = Settings()
