class Session:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def run(self, query, **kwargs):
        return []


class Driver:
    def __init__(self, uri, auth=None):
        self.uri = uri
        self.auth = auth

    def session(self):
        return Session()


class GraphDatabase:
    @staticmethod
    def driver(uri, auth=None):
        return Driver(uri, auth=auth)


__all__ = ["GraphDatabase"]
