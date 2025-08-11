import re
import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="./.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    API_V1_STR: str = "/api/v1"
    AUTH_STR: str = "/auth"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:80"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str = "Telegram Bot"
    PROJECT_VERSION: str = "0.1.0"

    # Telegram Bot Configuration
    BOT_TOKEN: str
    SUPERUSER_USERNAME: str
    SUPERUSER_USER_ID: int
    COMMUNICATION_STRATEGY: Literal["polling", "webhook"] = "polling"

    # Webhook Configuration
    WEBHOOK_URL: str = ""
    WEBHOOK_SSL_CERT: str = "./webhook_cert.pem"
    WEBHOOK_SSL_PRIVKEY: str = "./webhook_pkey.pem"
    
    # Antiflood Configuration
    ANTIFLOOD_ENABLED: bool = True
    ANTIFLOOD_RATE_LIMIT: int = 1  # Messages per second
    
    # Database Configuration
    DB_HOST: str = ""
    DB_PORT: int = 5432
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_NAME: str = ""
    
    # Plugins Configuration
    USE_PLUGINS: bool = False  # Enable plugins

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn | None:
        if not all([self.DB_HOST, self.DB_USER, self.DB_NAME]):
            return None
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_NAME,
        )

    # LLM API Keys
    FIREWORKS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    def _check_bot_token(self) -> None:
        regex = r"^[0-9]{10,}:[A-Za-z0-9_-]{35,}$"
        if self.BOT_TOKEN and not re.match(regex, self.BOT_TOKEN):
            raise ValueError(f"Invalid BOT_TOKEN format: {self.BOT_TOKEN}")

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("DB_PASSWORD", self.DB_PASSWORD)
        self._check_bot_token()
        return self


settings = Settings()
