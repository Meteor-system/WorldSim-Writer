from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    database_url: str = Field(alias='DATABASE_URL')
    secret_key: str = Field(alias='SECRET_KEY')
    access_token_expire_minutes: int = Field(default=1440, alias='ACCESS_TOKEN_EXPIRE_MINUTES')
    llm_base_url: AnyHttpUrl = Field(alias='LLM_BASE_URL')
    llm_api_key: str = Field(alias='LLM_API_KEY')
    llm_model: str = Field(alias='LLM_MODEL')
    llm_timeout_seconds: int = Field(default=60, alias='LLM_TIMEOUT_SECONDS')
    llm_mock: bool = Field(default=False, alias='LLM_MOCK')
    frontend_origin: str = Field(default='http://localhost:5173', alias='FRONTEND_ORIGIN')
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = Field(default='INFO', alias='LOG_LEVEL')
    db_connect_timeout_seconds: int = Field(default=5, ge=1, le=60, alias='DB_CONNECT_TIMEOUT_SECONDS')
    db_application_name: str = Field(
        default='worldsim-writer',
        min_length=1,
        max_length=55,
        pattern=r'^[A-Za-z0-9][A-Za-z0-9._:-]*$',
        alias='DB_APPLICATION_NAME',
    )
    db_pool_size: int = Field(default=5, ge=1, le=50, alias='DB_POOL_SIZE')
    db_max_overflow: int = Field(default=5, ge=0, le=50, alias='DB_MAX_OVERFLOW')
    db_pool_timeout_seconds: int = Field(default=5, ge=1, le=120, alias='DB_POOL_TIMEOUT_SECONDS')
    db_pool_recycle_seconds: int = Field(default=1800, ge=30, le=86400, alias='DB_POOL_RECYCLE_SECONDS')

    @field_validator('secret_key')
    @classmethod
    def reject_placeholder_secret(cls, value: str) -> str:
        if value == 'change-this-local-secret':
            raise ValueError('SECRET_KEY must be changed from the example value')
        return value

    @field_validator('log_level', mode='before')
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()


@lru_cache
def get_settings() -> Settings:
    return Settings()
