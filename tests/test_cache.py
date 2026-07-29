"""Tests for ResponseCache: key construction and get/set/TTL behavior."""
import time

from rejestr_io_mcp.cache import ResponseCache


def test_make_key_is_order_independent_for_params():
    key_a = ResponseCache.make_key("GET", "org", {"nazwa": "Acme", "strona": 1})
    key_b = ResponseCache.make_key("GET", "org", {"strona": 1, "nazwa": "Acme"})
    assert key_a == key_b


def test_make_key_differs_for_different_params():
    key_a = ResponseCache.make_key("GET", "org", {"strona": 1})
    key_b = ResponseCache.make_key("GET", "org", {"strona": 2})
    assert key_a != key_b


def test_get_returns_none_for_missing_key():
    cache = ResponseCache(maxsize=10, ttl=60)
    assert cache.get(ResponseCache.make_key("GET", "org", {})) is None


def test_set_then_get_returns_cached_value():
    cache = ResponseCache(maxsize=10, ttl=60)
    key = ResponseCache.make_key("GET", "org/1", {})
    cache.set(key, {"id": 1})
    assert cache.get(key) == {"id": 1}


def test_entry_expires_after_ttl():
    cache = ResponseCache(maxsize=10, ttl=0.05)
    key = ResponseCache.make_key("GET", "org/1", {})
    cache.set(key, {"id": 1})
    time.sleep(0.1)
    assert cache.get(key) is None
