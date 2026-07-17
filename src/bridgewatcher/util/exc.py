class BridgewatcherError(Exception): ...


class PriceProviderError(BridgewatcherError): ...


class UncraftableItemCraftedError(BridgewatcherError): ...


class InsufficientDataError(BridgewatcherError): ...


class NoItemFoundError(BridgewatcherError):
    def __init__(self, message: str, item_name: str, *args) -> None:
        super().__init__(message, *args)
        self.item_name = item_name


class UntrackedItemRequested(BridgewatcherError): ...
