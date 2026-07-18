from datetime import datetime, timezone
from typing import Any

from bridgewatcher.db import db
from bridgewatcher.db.schema import ItemName
from bridgewatcher.util.exc import NoItemFoundError


class Markdown:
    def italic(self, s: Any) -> str:
        return f"*{str(s)}*"

    def bold(self, s: Any) -> str:
        return f"**{str(s)}**"

    def bold_italic(self, s: Any) -> str:
        return f"***{str(s)}***"

    def inline_code(self, s: Any) -> str:
        return f"`{str(s)}`"

    def underline(self, s: Any) -> str:
        return f"__{str(s)}__"

    def strikethrough(self, s: Any) -> str:
        return f"~~{str(s)}~~"

    def spoiler(self, s: Any) -> str:
        return f"||{str(s)}||"

    def link(self, display: str, url: str) -> str:
        return f"[{display}]({url})"


def get_datetime_from_timestamp(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S").replace(
        tzinfo=timezone.utc
    )


def readable_timestamp(timestamp: str) -> str:
    time = get_datetime_from_timestamp(timestamp)
    return f"{time.day:02d}/{time.month:02d}/{time.year} at {time.hour:02d}:{time.minute:02d}"


def format_number(n: int) -> str:
    return f"{n:,}"


async def get_item_name_by_id(item_id: str) -> ItemName:
    names = db.get_collection("item_names")
    name = await names.find_one({"id": item_id})
    if name is None:
        raise NoItemFoundError(f"{item_id} doesn't exist", item_id)
    return ItemName.from_mongo(name)
