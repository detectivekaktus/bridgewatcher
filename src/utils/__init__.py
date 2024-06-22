#!/usr/bin/env python3
from typing import Callable, Type


def overrides(interface_class: Type) -> Callable:
    def overrider(method: Callable) -> Callable:
        assert method.__name__ in dir(interface_class), f"{method.__name__} does not override any method in {interface_class.__name__}"
        return method
    return overrider


def strtoquality_int(quality: str) -> int:
    match quality.lower():
        case "normal":
            return 1
        case "good":
            return 2
        case "outstanding":
            return 3
        case "excellent":
            return 4
        case "masterpiece":
            return 5
        case _:
            return 1


def api_name_to_reable_name(item_names: dict[str, str], name: str) -> str:
    return list(item_names.keys())[list(item_names.values()).index(name)]


def strtoint_server(server: str) -> int:
    match server.lower():
        case "america":
            return 1
        case "europe":
            return 2
        case "asia":
            return 3
        case _:
            return 1


def inttostr_server(server: int) -> str:
    match server:
        case 1:
            return "america"
        case 2:
            return "europe"
        case 3:
            return "asia"
        case _:
            return "america"


def inttoemoji_server(server: int) -> str:
    match server:
        case 1:
            return "🇺🇸"
        case 2:
            return "🇪🇺"
        case 3:
            return "🇨🇳"
        case _:
            return "🇺🇸"
