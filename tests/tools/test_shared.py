"""Tests for shared tool helpers: enum translation and PDF file saving."""
from pathlib import Path

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from rejestr_io_mcp.tools._shared import enum_param, save_pdf, wrap_scalar_result

_TEST_MAP = {"micro": "mikro", "small": "mala"}


def test_enum_param_returns_translated_value():
    assert enum_param("micro", _TEST_MAP, "size") == "mikro"


def test_enum_param_raises_tool_error_for_unknown_value():
    with pytest.raises(ToolError, match="huge"):
        enum_param("huge", _TEST_MAP, "size")


async def test_save_pdf_creates_download_dir_if_missing(tmp_path):
    download_dir = str(tmp_path / "downloads")
    file_path = await save_pdf(download_dir, "krs_extract", "12345", b"%PDF-1.4 fake")
    assert Path(file_path).exists()
    assert Path(file_path).read_bytes() == b"%PDF-1.4 fake"


async def test_save_pdf_returns_absolute_path_with_expected_naming(tmp_path):
    download_dir = str(tmp_path / "downloads")
    file_path = await save_pdf(download_dir, "krs_extract", "12345", b"content")
    assert Path(file_path).is_absolute()
    name = Path(file_path).name
    assert name.startswith("krs_extract_12345_")
    assert name.endswith(".pdf")


async def test_save_pdf_raises_tool_error_when_directory_is_not_writable(tmp_path, monkeypatch):
    def deny_mkdir(self, *args, **kwargs):
        raise OSError(13, "Permission denied")

    monkeypatch.setattr(Path, "mkdir", deny_mkdir)
    download_dir = str(tmp_path / "downloads")

    with pytest.raises(ToolError) as excinfo:
        await save_pdf(download_dir, "krs_extract", "12345", b"%PDF-1.4 fake")

    message = str(excinfo.value)
    assert download_dir in message
    assert "REJESTR_IO_DOWNLOAD_DIR" in message


async def test_save_pdf_raises_tool_error_when_write_fails(tmp_path, monkeypatch):
    def deny_write(self, *args, **kwargs):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(Path, "write_bytes", deny_write)
    download_dir = str(tmp_path / "downloads")

    with pytest.raises(ToolError) as excinfo:
        await save_pdf(download_dir, "krs_extract", "12345", b"%PDF-1.4 fake")

    message = str(excinfo.value)
    assert download_dir in message
    assert "No space left on device" in message


async def test_wrap_scalar_result_unwraps_to_plain_scalar_on_client():
    mcp = FastMCP("test-server")

    @mcp.tool
    async def get_path():
        return wrap_scalar_result("/tmp/downloads/krs_extract_12345.pdf")

    async with Client(mcp) as client:
        result = await client.call_tool("get_path", {})

    assert result.data == "/tmp/downloads/krs_extract_12345.pdf"
