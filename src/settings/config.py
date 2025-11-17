from __future__ import annotations

import json
import os
from enum import Enum
from functools import lru_cache
from importlib import import_module
from typing import ClassVar, TypeAlias, TypeVar, Union


_pydantic = import_module("pydantic")
Field = getattr(_pydantic, "Field")
field_validator = getattr(_pydantic, "field_validator")
BaseSettings = getattr(import_module("pydantic_settings"), "BaseSettings")


class EnvironmentType(str, Enum):
    """Доступные окружения приложения."""

    PROD = "prod"
    TEST = "test"
    DEV = "dev"
    LOCAL = "local"


def _parse_list(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value

    text = value.strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    return [item.strip() for item in text.split(",") if item.strip()]


class BaseConfig(BaseSettings):
    """Базовые настройки приложения."""

    ENV_TYPE: EnvironmentType = Field(env="ENV_TYPE", default=EnvironmentType.LOCAL)
    DEBUG: bool = Field(env="DEBUG", default=False)
    SECRET_KEY: str = Field(env="SECRET_KEY", default="change-me")

    ALLOWED_HOSTS: list[str] = Field(env="ALLOWED_HOSTS", default=["*"])
    CSRF_TRUSTED_ORIGINS: list[str] = Field(
        env="CSRF_TRUSTED_ORIGINS",
        default=["http://localhost:8000"],
    )

    DB_NAME: str = Field(env="DB_NAME", default="tsos")
    DB_USER: str = Field(env="DB_USER", default="tsos_user")
    DB_PASSWORD: str = Field(env="DB_PASSWORD", default="change_me")
    DB_HOST: str = Field(env="DB_HOST", default="localhost")
    DB_PORT: int = Field(env="DB_PORT", default=5432)
    DB_POOL_MIN: int = Field(env="DB_POOL_MIN", default=1)
    DB_POOL_MAX: int = Field(env="DB_POOL_MAX", default=5)

    OPENAI_API_KEY: str | None = Field(env="OPENAI_API_KEY", default=None)
    OLLAMA_API_KEY: str | None = Field(env="OLLAMA_API_KEY", default=None)
    G4F_API_KEY: str | None = Field(env="G4F_API_KEY", default=None)
    OPENROUTER_API_KEY: str | None = Field(env="OPENROUTER_API_KEY", default=None)
    API_HOST: str = Field(env="API_HOST", default="0.0.0.0")
    API_PORT: int = Field(env="API_PORT", default=8000)
    SUMMARY_PROMPT: str = Field(
        env="SUMMARY_PROMPT",
        default="Опиши подробно сцену на кадре, перечисли действия людей.",
    )
    PEOPLE_COUNT_PROMPT: str = Field(
        env="PEOPLE_COUNT_PROMPT",
        default="Сколько уникальных людей на изображении? Ответь только числом.",
    )
    METRICS_NAMESPACE: str = Field(env="METRICS_NAMESPACE", default="tsos")

    class Config:
        env_file: ClassVar[str] = ".env"
        env_file_encoding: ClassVar[str] = "utf-8"
        case_sensitive: ClassVar[bool] = False

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def _validate_allowed_hosts(cls, value: str | list[str]) -> list[str]:
        return _parse_list(value)

    @field_validator("CSRF_TRUSTED_ORIGINS", mode="before")
    @classmethod
    def _validate_csrf_trusted_origins(cls, value: str | list[str]) -> list[str]:
        return _parse_list(value)

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


class LocalConfig(BaseConfig):
    DEBUG: bool = True


class DevConfig(BaseConfig):
    DEBUG: bool = False


class TestConfig(BaseConfig):
    DEBUG: bool = True


class ProdConfig(BaseConfig):
    DEBUG: bool = False


ConfigType = TypeVar("ConfigType", bound=BaseConfig)
ConfigUnion: TypeAlias = Union[LocalConfig, DevConfig, TestConfig, ProdConfig]

_CONFIG_MAP: dict[EnvironmentType, type[BaseConfig]] = {
    EnvironmentType.LOCAL: LocalConfig,
    EnvironmentType.DEV: DevConfig,
    EnvironmentType.TEST: TestConfig,
    EnvironmentType.PROD: ProdConfig,
}


def _resolve_environment(env: str | None = None) -> EnvironmentType:
    raw_env = (env or os.getenv("ENV_TYPE") or EnvironmentType.LOCAL.value).lower()
    for env_type in EnvironmentType:
        if raw_env == env_type.value:
            return env_type
    return EnvironmentType.LOCAL


@lru_cache(maxsize=1)
def get_settings(env: str | None = None) -> ConfigUnion:
    env_type = _resolve_environment(env)
    config_cls = _CONFIG_MAP[env_type]
    return config_cls()


__all__ = [
    "EnvironmentType",
    "BaseConfig",
    "LocalConfig",
    "DevConfig",
    "TestConfig",
    "ProdConfig",
    "ConfigUnion",
    "get_settings",
]
