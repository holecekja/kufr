import pathlib
from typing import *

class CachedFile:
    # TODO: Binary file support?
    def __init__(self, path:str):
        self.path = pathlib.Path(path)
        self.timestamp = None
        self.cachedData = None

    def read(self) -> List[AnyStr]:
        if not self.path.exists():
            return []

        if self.timestamp is None or self.path.stat().st_mtime != self.timestamp:
            self.timestamp = self.path.stat().st_mtime

            with self.path.open(encoding="utf-8") as f:
                self.cachedData = f.read().splitlines()

        return self.cachedData

    def write(self, data:List[AnyStr]):
        self.cachedData = data
        with self.path.open("w", encoding="utf-8") as f:
            f.write("\n".join(data))

        self.timestamp = self.path.stat().st_mtime
