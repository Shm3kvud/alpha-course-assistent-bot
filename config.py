from functools import lru_cache

from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    # пути бд откуда читаем (данные что нам дали, альфа курсы)
    source_database_url: PostgresDsn
    app_database_url: PostgresDsn

    # векторная бд
    vector_database_url: PostgresDsn
    collection_name: str = "courses"

    # модель эмбеддингов, 2 вариации, определяется при старте из условий
    # размер батча и на чем работает
    embedding_model: str = "intfloat/multilingual-e5-large"
    embedding_fallback_model: str = "intfloat/multilingual-e5-small"
    embedding_batch_size: int = Field(16, gt=0)
    embedding_device: str = "cpu"

    # для retrieval.py
    top_k: int = Field(5, gt=0)
    score_threshold: float = Field(0.7, ge=0, le=1)

    # токен бота
    bot_token: SecretStr | None = None

    # текстовая модель гигачата, апи, само название модели
    # право доступа персональное (физ лицо)
    #
    gigachat_api_key: SecretStr | None = None
    gigachat_model: str = "GigaChat-2"
    gigachat_scope: str = "GIGACHAT_API_PERS"


@lru_cache
def get_settings() -> Settings:
    return Settings()