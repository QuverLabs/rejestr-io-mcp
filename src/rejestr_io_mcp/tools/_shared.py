"""Helpers shared by MCP tool modules: error translation, enum translation, and PDF file saving."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, TypeVar

from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from fastmcp.utilities.types import File

from ..errors import RejestrIoError
from ..mappings import translate_enum

T = TypeVar("T")


async def call_api(coro: Awaitable[T]) -> T:
    """Await a client call, translating RejestrIoError into a ToolError."""
    try:
        return await coro
    except RejestrIoError as exc:
        raise ToolError(str(exc)) from exc


def enum_param(value: str, mapping: dict[str, str], field_name: str) -> str:
    try:
        return translate_enum(value, mapping, field_name)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc


async def save_pdf(download_dir: str, document_type: str, org_id: str, content: bytes) -> str:
    directory = Path(download_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    file_path = directory / f"{document_type}_{org_id}_{timestamp}.pdf"

    def _write() -> None:
        directory.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

    try:
        await asyncio.to_thread(_write)
    except OSError as exc:
        raise ToolError(
            f"Could not save the PDF to {download_dir!r}: {exc}. "
            "Set REJESTR_IO_DOWNLOAD_DIR to a writable absolute path."
        ) from exc
    return str(file_path.resolve())


def wrap_scalar_result(value: str) -> ToolResult:
    """Wrap a plain scalar return value the way FastMCP itself would if the tool
    had an inferred output schema. Needed because a tool annotated `-> Any` gets
    no output_schema at all, so a bare non-dict return produces no
    structuredContent on the wire and the client's result.data stays None.
    """
    return ToolResult(
        content=value,
        structured_content={"result": value},
        meta={"fastmcp": {"wrap_result": True}},
    )


async def build_pdf_tool_result(
    download_dir: str,
    document_type: str,
    org_id: str,
    content: bytes,
    return_base64: bool,
    file_name: str,
) -> Any:
    file_path = await save_pdf(download_dir, document_type, org_id, content)
    if return_base64:
        return ToolResult(
            content=[file_path, File(data=content, format="pdf", name=file_name)],
            structured_content={"file_path": file_path},
        )
    return wrap_scalar_result(file_path)
