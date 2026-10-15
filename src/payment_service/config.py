from functools import lru_cache

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    name: str
    username: str
    password: SecretStr
    host: str
    port: int

    @property
    def url(self) -> str:
        return (
            f'postgresql+asyncpg://'
            f'{self.username}:{self.password.get_secret_value()}'
            f'@{self.host}:{self.port}/{self.name}'
        )


class RabbitMQSettings(BaseModel):
    url: str
    exchange: str


class OutboxRabbitMQSettings(BaseModel):
    attempts_maximum: int = 3
    batch_limit: int = 50
    dispatch_interval_seconds: float = 5.0


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_nested_delimiter='__',
        extra='ignore',
    )

    api_key: SecretStr = Field(min_length=1)

    postgres: DatabaseSettings
    rabbitmq: RabbitMQSettings
    outbox_rabbitmq: OutboxRabbitMQSettings = Field(
        default_factory=OutboxRabbitMQSettings
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
