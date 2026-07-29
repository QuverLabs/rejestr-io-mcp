"""Tests for English<->Polish enum and parameter-name mapping tables."""
import pytest

from rejestr_io_mcp.mappings import (
    ADDRESS_TYPE_MAP,
    CHAPTER_MAP,
    EXTRACT_TYPE_MAP,
    RELATION_STATUS_MAP,
    SEARCH_ORGANIZATIONS_PARAM_MAP,
    SIZE_MAP,
    translate_enum,
)


def test_translate_enum_returns_polish_value():
    assert translate_enum("micro", SIZE_MAP, "size") == "mikro"


def test_translate_enum_raises_value_error_with_allowed_values():
    with pytest.raises(ValueError, match="micro"):
        translate_enum("huge", SIZE_MAP, "size")


def test_size_map_has_all_four_values():
    assert set(SIZE_MAP) == {"large_medium", "small", "micro", "ngo"}


def test_address_type_map_has_all_three_values():
    assert set(ADDRESS_TYPE_MAP) == {"any", "organization", "branch"}


def test_chapter_map_has_all_six_chapters():
    assert set(CHAPTER_MAP) == {
        "general", "branches", "shares", "mentions", "liabilities", "transformations",
    }


def test_extract_type_map_has_both_values():
    assert set(EXTRACT_TYPE_MAP) == {"current", "full"}


def test_relation_status_map_has_both_values():
    assert set(RELATION_STATUS_MAP) == {"current", "historical"}


def test_search_organizations_param_map_covers_all_26_parameters():
    assert len(SEARCH_ORGANIZATIONS_PARAM_MAP) == 28
    assert SEARCH_ORGANIZATIONS_PARAM_MAP["name"] == "nazwa"
    assert SEARCH_ORGANIZATIONS_PARAM_MAP["page_size"] == "ile_na_strone"
