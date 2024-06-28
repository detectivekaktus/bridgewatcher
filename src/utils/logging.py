#!/usr/bin/env python3
from datetime import datetime
from logging import DEBUG, FileHandler, Formatter, Logger, StreamHandler
from os import path, mkdir


class BotLogger(Logger):
    def __init__(self, name: str, filename: str, level: int = DEBUG) -> None:
        super().__init__(name=name, level=level)
        
        formatter: Formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s",
                                         datefmt="%d/%m/%Y %I:%M:%S %p")
        fileHandler: FileHandler = FileHandler(filename)
        fileHandler.setFormatter(formatter)
        console: StreamHandler = StreamHandler()
        console.setLevel(DEBUG)
        console.setFormatter(formatter)

        self.addHandler(console)
        self.addHandler(fileHandler)


def get_logger() -> BotLogger:
    if not path.exists("logs/"):
        mkdir("logs/")
    return BotLogger("bridgewatcher", f"logs/{datetime.now().strftime("%d.%m.%Y")}")
