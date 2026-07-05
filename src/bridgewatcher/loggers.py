from json import loads
from logging import getLogger
from logging.config import dictConfig
from pathlib import Path


def load_logging_config() -> None:
    conf_path = Path(__file__).parent.parent.parent / "logging.conf.json"
    with conf_path.open("r") as f:
        content = f.read()

    conf = loads(content)
    if "file" in conf.get("handlers", {}):
        filename = conf["handlers"]["file"].get("filename")
        if filename:
            log_dir = conf_path.parent / Path(filename).parent
            log_dir.mkdir(parents=True, exist_ok=True)

    dictConfig(config=conf)


LOGGER = getLogger("bridgewatcher")

__all__ = ("LOGGER",)
