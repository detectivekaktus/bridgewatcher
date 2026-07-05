from bridgewatcher.db.seed.run import seed_if_needed_sync
from bridgewatcher.loggers import load_logging_config


def main() -> None:
    seed_if_needed_sync()

    load_logging_config()
    print("Starting over")


if __name__ == "__main__":
    main()
