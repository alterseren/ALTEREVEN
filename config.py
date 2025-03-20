from dataclasses import dataclass
from environs import Env


@dataclass
class BotConfig:
    token: str


@dataclass
class DbConfig:
    path: str


@dataclass
class CacheConfig:
    ttl: int


@dataclass
class Config:
    bot: BotConfig
    db: DbConfig
    cache: CacheConfig


def load_config() -> Config:
    env = Env()
    env.read_env()

    return Config(
        bot=BotConfig(
            token=env.str("BOT_TOKEN"),
        ),
        db=DbConfig(
            path=env.str("DB_PATH", "bot.db"),
        ),
        cache=CacheConfig(
            ttl=env.int("CACHE_TTL", 3600),  
        ),
    )

