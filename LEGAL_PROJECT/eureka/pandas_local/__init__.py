class DataFrame:
    def __init__(self, *args, **kwargs):
        self._data = kwargs.get("data", [])

    def __getitem__(self, key):
        return self

    def __len__(self):
        return len(self._data)

    def copy(self):
        return DataFrame(data=self._data)

    def to_dict(self, orient="records"):
        return list(self._data)

    @staticmethod
    def from_records(rows):
        return DataFrame(data=rows)


class Series:
    def __init__(self, data=None):
        self._data = data or []

    def isin(self, values):
        return self

    def notna(self):
        return self


def read_csv(*args, **kwargs):
    return DataFrame(data=[])


__all__ = ["DataFrame", "Series", "read_csv"]
