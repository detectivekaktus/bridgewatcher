#!/usr/bin/env python3
from typing import Type, Callable


def overrides(interface_class: Type) -> Callable:
    def overrider(method: Callable) -> Callable:
        assert method.__name__ in dir(
            interface_class
        ), f"{method.__name__} does not override any method in {interface_class.__name__}"
        return method

    return overrider
