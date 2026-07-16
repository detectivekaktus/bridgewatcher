from datetime import datetime
from typing import Any

from bridgewatcher.api.model import Qualities


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


def readable_timestamp(timestamp: str) -> str:
    time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    return f"{time.day:02d}/{time.month:02d}/{time.year} at {time.hour:02d}:{time.minute:02d}"


def format_number(n: int) -> str:
    return f"{n:,}"


# not sure if this function belongs to this file
def get_item_icon(item_id: str, quality: Qualities = Qualities.NORMAL) -> str:
    return f"https://render.albiononline.com/v1/item/{item_id}?quality={quality.value}"
