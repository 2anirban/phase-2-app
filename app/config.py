"""Load settings from the environment and the optional project-root .env file."""

from pathlib import Path

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PowerShell environment variables override values in .env and these defaults.
    environment: str = Field(default="local", min_length=1)
    app_version: str = Field(default="dev", min_length=1)
    github_token: SecretStr | None = None
    github_api_base: AnyHttpUrl = AnyHttpUrl("https://api.github.com")
    outbound_timeout_s: float = Field(default=5.0, gt=0, allow_inf_nan=False)

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
