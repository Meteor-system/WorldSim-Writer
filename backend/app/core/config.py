from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8-sig', extra='forbid')

    database_url: str = Field(alias='DATABASE_URL')
    secret_key: str = Field(alias='SECRET_KEY')
    access_token_expire_minutes: int = Field(default=1440, alias='ACCESS_TOKEN_EXPIRE_MINUTES')
    llm_base_url: AnyHttpUrl = Field(alias='LLM_BASE_URL')
    llm_api_key: str = Field(alias='LLM_API_KEY')
    llm_model: str = Field(alias='LLM_MODEL')
    llm_api_mode: Literal['responses', 'chat_completions'] = Field(default='responses', alias='LLM_API_MODE')
    llm_timeout_seconds: int = Field(default=60, ge=1, le=300, alias='LLM_TIMEOUT_SECONDS')
    llm_read_timeout_seconds: int = Field(default=300, ge=1, le=1800, alias='LLM_READ_TIMEOUT_SECONDS')
    llm_mock: bool = Field(default=False, alias='LLM_MOCK')
    frontend_origin: str = Field(default='http://localhost:5173', alias='FRONTEND_ORIGIN')
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = Field(default='INFO', alias='LOG_LEVEL')
    api_host: str = Field(default='127.0.0.1', alias='API_HOST')
    api_port: str = Field(default='8000', alias='API_PORT')
    api_workers: str = Field(default='1', alias='API_WORKERS')
    api_backlog: str = Field(default='2048', alias='API_BACKLOG')
    api_limit_concurrency: str = Field(default='100', alias='API_LIMIT_CONCURRENCY')
    api_timeout_keep_alive_seconds: str = Field(default='5', alias='API_TIMEOUT_KEEP_ALIVE_SECONDS')
    api_timeout_graceful_shutdown_seconds: str = Field(
        default='30',
        alias='API_TIMEOUT_GRACEFUL_SHUTDOWN_SECONDS',
    )
    api_proxy_headers: str = Field(default='false', alias='API_PROXY_HEADERS')
    api_forwarded_allow_ips: str = Field(default='127.0.0.1', alias='API_FORWARDED_ALLOW_IPS')
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
