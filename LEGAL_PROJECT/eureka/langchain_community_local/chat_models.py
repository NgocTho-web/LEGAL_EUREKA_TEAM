class ChatOllama:
    def __init__(self, *args, **kwargs):
        self.model = kwargs.get("model")
        self.base_url = kwargs.get("base_url")
        self.temperature = kwargs.get("temperature")


__all__ = ["ChatOllama"]
