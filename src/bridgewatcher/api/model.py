from dataclasses import dataclass
from enum import IntEnum, StrEnum


class Qualities(IntEnum):
    NORMAL = 1
    GOOD = 2
    OUTSTANDING = 3
    EXCELLENT = 4
    MASTERPIECE = 5

    @staticmethod
    def from_int(n: int) -> "Qualities":
        try:
            return Qualities(n)
        except ValueError:
            return Qualities.NORMAL


class Cities(StrEnum):
    BLACK_MARKET = "black market"
    BRECILIEN = "brecilien"
    BRIDGEWATCH = "bridgewatch"
    CAERLEON = "caerleon"
    FORT_STERLING = "fort sterling"
    LYMHURST = "lymhurst"
    MARTLOCK = "martlock"
    THETFORD = "thetford"

    @staticmethod
    def from_str(s: str) -> "Cities":
        try:
            return Cities(s.lower())
        except ValueError:
            return Cities.BLACK_MARKET


@dataclass
class CityPrice:
    item_id: str
    city: str
    quality: int

    # these namings come directly from the albion online data project
    # api, so i don't want to confuse anybody by giving different names
    sell_price_min: int  # top of the sell orders
    sell_price_min_date: str
    sell_price_max: int  # bottom of the sell orders
    sell_price_max_date: str

    buy_price_min: int  # bottom of the buy orders
    buy_price_min_date: str
    buy_price_max: int  # top of the buy orders
    buy_price_max_date: str


@dataclass
class GoldPrice:
    price: int
    timestamp: str
