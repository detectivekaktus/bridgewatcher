from bridgewatcher.api.model import Qualities


def get_item_icon(item_id: str, quality: Qualities = Qualities.NORMAL) -> str:
    return f"https://render.albiononline.com/v1/item/{item_id}?quality={quality.value}"
