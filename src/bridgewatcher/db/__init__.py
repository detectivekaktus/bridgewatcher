from os import getenv
from sys import stderr
from urllib.parse import quote

from dotenv import load_dotenv
from pymongo import AsyncMongoClient
from redis import Redis

load_dotenv()

_MONGO_USER = getenv("MONGO_USERNAME")
_MONGO_PASSWORD = getenv("MONGO_PASSWORD")
_MONGO_HOST = getenv("MONGO_HOST")
_MONGO_PORT = getenv("MONGO_PORT")

_MONGO_DB = getenv("MONGO_DB")

if not all((_MONGO_USER, _MONGO_PASSWORD, _MONGO_HOST, _MONGO_PORT)):
    print(
        "FATAL: MongoDB is not setup properly. See .env.example for environment variables expected",
        file=stderr,
    )
    exit(1)

connection_string = f"mongodb://{quote(_MONGO_USER)}:{quote(_MONGO_PASSWORD)}@{quote(_MONGO_HOST)}:{_MONGO_PORT}/?authSource=admin"  # type: ignore

client = AsyncMongoClient(connection_string)
db = client.get_database(_MONGO_DB)


_REDIS_HOST = getenv("REDIS_HOST")
_REDIS_PORT = getenv("REDIS_PORT")
_REDIS_PASSWORD = getenv("REDIS_PASSWORD")

if not all((_REDIS_HOST, _REDIS_PORT, _REDIS_PASSWORD)):
    print(
        "FATAL: Redis is not setup properly. See .env.example for environment variables expected",
        file=stderr,
    )
    exit(1)

redis = Redis(host=_REDIS_HOST, port=_REDIS_PORT, password=_REDIS_PASSWORD)  # type: ignore

__all__ = ("client", "db", "redis")
