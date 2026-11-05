class CORSMiddleware:
    def __init__(self, *args, **kwargs):
        pass


class FastAPI:
    def __init__(self, *args, **kwargs):
        self.title = kwargs.get("title", "")

    def add_middleware(self, *args, **kwargs):
        return None

    def include_router(self, *args, **kwargs):
        return None


class APIRouter:
    def __init__(self, *args, **kwargs):
        self.routes = []

    def post(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator


__all__ = ["FastAPI", "APIRouter", "CORSMiddleware"]
