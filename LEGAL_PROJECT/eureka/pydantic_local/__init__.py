from typing import Any, Callable, Optional


class BaseModel:
    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class FieldInfo:
    def __init__(self, *args, **kwargs):
        self.default = kwargs.get("default", None)
        self.description = kwargs.get("description", "")


def Field(default=..., *args, **kwargs):
    return default


__all__ = ["BaseModel", "Field"]
