from bridgewatcher.db.seed.run import seed_if_needed_sync


def main() -> None:
    seed_if_needed_sync()
    print("Starting over")


if __name__ == "__main__":
    main()
