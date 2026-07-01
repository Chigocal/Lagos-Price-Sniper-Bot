from src.services.query_cleaner import standardize_search_query


def test_returns_raw_when_no_api_key(monkeypatch):
    monkeypatch.setattr("src.services.query_cleaner.settings.gemini_api_key", "")
    result = standardize_search_query("redmi note 10")
    assert result == "redmi note 10"
