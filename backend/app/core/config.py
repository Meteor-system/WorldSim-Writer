from functools import lru_cache

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

    @field_validator('secret_key')
    @classmethod
    def reject_placeholder_secret(cls, value: str) -> str:
        if value == 'change-this-local-secret':
            raise ValueError('SECRET_KEY must be changed from the example value')
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
