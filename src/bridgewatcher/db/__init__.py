from os import getenv
from sys import stderr
from urllib.parse import quote

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

load_dotenv()

_MONGO_USER = getenv("MONGO_USERNAME")
_MONGO_PASSWORD = getenv("MONGO_PASSWORD")
_MONGO_HOST = getenv("MONGO_HOST")
_MONGO_PORT = getenv("MONGO_PORT")

_MONGO_DB = getenv("MONGO_DB")

if not all((_MONGO_USER, _MONGO_PASSWORD, _MONGO_HOST, _MONGO_PORT)):
    print(
        "FATAL: MongoDB is not setup properly. See .env.example for environment variables expected.",
        file=stderr,
    )
    exit(1)

connection_string = f"mongodb://{quote(_MONGO_USER)}:{quote(_MONGO_PASSWORD)}@{quote(_MONGO_HOST)}:{_MONGO_PORT}/?authSource=admin"  # type: ignore

client = AsyncMongoClient(connection_string)
db = client.get_database(_MONGO_DB)

__all__ = ("client", "db")
