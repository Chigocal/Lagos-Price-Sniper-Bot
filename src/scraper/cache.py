import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CACHE_PATH = DATA_DIR / "search_cache.json"


class SearchCache:
    def __init__(self, path: str | Path = CACHE_PATH):
        self.path = Path(path)
        self._cache: dict[str, str] | None = None

    def _load(self) -> dict[str, str]:
        if self._cache is not None:
            return self._cache
        if self.path.exists():
            self._cache = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self._cache = {}
        return self._cache

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._cache, indent=4), encoding="utf-8")

    def get(self, raw_query: str) -> str | None:
        return self._load().get(raw_query)

    def set(self, raw_query: str, cleaned: str):
        self._load()[raw_query] = cleaned
        self._save()


search_cache = SearchCache()
