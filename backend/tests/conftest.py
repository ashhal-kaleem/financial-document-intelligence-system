import os
import pytest

# Dummy settings so the app imports without real keys. Real keys override these.
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")


def pytest_configure(config):
    config.addinivalue_line("markers", "live: needs real service keys and network")


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_LIVE_TESTS") == "1":
        return
    skip = pytest.mark.skip(reason="live test: set RUN_LIVE_TESTS=1 with real keys")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)
