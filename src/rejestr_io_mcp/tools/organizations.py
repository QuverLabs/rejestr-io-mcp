"""MCP tools for organization data: search, KRS chapters, relations, extracts, and entries."""
from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from ..client import RejestrIoClient
from ..mappings import (
    ADDRESS_TYPE_MAP,
    CHAPTER_MAP,
    EXTRACT_TYPE_MAP,
    RELATION_STATUS_MAP,
    SEARCH_ORGANIZATIONS_PARAM_MAP,
    SIZE_MAP,
)
from ._shared import RETURN_BASE64_DESC, build_pdf_tool_result, build_query_params, call_api, enum_param


def register(mcp: FastMCP, client: RejestrIoClient, download_dir: str) -> None:
    @mcp.tool
    async def search_organizations(
        name: Annotated[
            str | None, Field(description="Fragment of the organization name to search for (substring match).")
        ] = None,
        nip: Annotated[str | None, Field(description="Full NIP number, without dashes.")] = None,
        regon: Annotated[str | None, Field(description="Full REGON number.")] = None,
        legal_form: Annotated[
            str | None, Field(description="Full legal form, in uppercase, as recorded in KRS.")
        ] = None,
        first_entry_date: Annotated[
            str | None,
            Field(description="Date of the organization's first KRS entry. Format: YYYY-MM-DD."),
        ] = None,
        latest_entry_date: Annotated[
            str | None,
            Field(description="Date of the organization's most recent KRS entry. Format: YYYY-MM-DD."),
        ] = None,
        primary_pkd_code: Annotated[
            str | None,
            Field(description="PKD code of the organization's primary (przeważający) business activity."),
        ] = None,
        secondary_pkd_code: Annotated[
            str | None, Field(description="PKD code of a secondary business activity.")
        ] = None,
        any_pkd_code: Annotated[
            str | None, Field(description="PKD code matching either the primary or a secondary business activity.")
        ] = None,
        is_public_benefit_org: Annotated[
            bool | None, Field(description="Whether the organization has public benefit organization (OPP) status.")
        ] = None,
        is_deregistered: Annotated[
            bool | None, Field(description="Whether the organization has been deregistered (wykreślona) from KRS.")
        ] = None,
        is_in_liquidation: Annotated[
            bool | None, Field(description="Whether the organization is in liquidation.")
        ] = None,
        is_in_bankruptcy: Annotated[
            bool | None, Field(description="Whether the organization is in bankruptcy proceedings.")
        ] = None,
        is_suspended: Annotated[
            bool | None, Field(description="Whether the organization's business activity is suspended.")
        ] = None,
        share_capital: Annotated[str | None, Field(description="Share capital amount.")] = None,
        size: Annotated[
            str | None,
            Field(
                description=(
                    "Organization size classification per the Polish Accounting Act: "
                    "one of 'large_medium', 'small', 'micro', 'ngo'."
                )
            ),
        ] = None,
        address_type: Annotated[
            str | None,
            Field(
                description=(
                    "Which address to match against: one of 'any' (default), 'organization', 'branch'."
                )
            ),
        ] = None,
        country: Annotated[
            str | None, Field(description="Country in the organization's or branch's address.")
        ] = None,
        city: Annotated[str | None, Field(description="City in the organization's or branch's address.")] = None,
        postal_code: Annotated[
            str | None, Field(description="Postal code in the organization's or branch's address.")
        ] = None,
        street: Annotated[str | None, Field(description="Street in the organization's or branch's address.")] = None,
        house_number: Annotated[
            str | None, Field(description="House/building number in the organization's or branch's address.")
        ] = None,
        terc_province: Annotated[
            str | None, Field(description="Two-digit TERC code of the voivodeship (province).")
        ] = None,
        terc_county: Annotated[
            str | None, Field(description="Four-digit TERC code of the county (powiat).")
        ] = None,
        terc_municipality: Annotated[
            str | None, Field(description="Six-digit TERC code of the municipality (gmina).")
        ] = None,
        sort_by: Annotated[
            str | None,
            Field(
                description=(
                    "Sort order for results. Default (if unset): sorted by text match to 'name' when given "
                    "(tie-broken by higher share capital), otherwise by descending KRS number."
                )
            ),
        ] = None,
        page: Annotated[int | None, Field(description="Page number of results, starting at 1. Default: 1.")] = None,
        page_size: Annotated[
            int | None, Field(description="Number of results per page. Default: 10.")
        ] = None,
    ) -> dict:
        """Search organizations in the Polish National Court Register (KRS) by name, registry numbers, legal form, PKD codes, status flags, address, and pagination."""
        params = build_query_params(
            SEARCH_ORGANIZATIONS_PARAM_MAP,
            name=name, nip=nip, regon=regon, legal_form=legal_form,
            first_entry_date=first_entry_date, latest_entry_date=latest_entry_date,
            primary_pkd_code=primary_pkd_code, secondary_pkd_code=secondary_pkd_code,
            any_pkd_code=any_pkd_code, is_public_benefit_org=is_public_benefit_org,
            is_deregistered=is_deregistered, is_in_liquidation=is_in_liquidation,
            is_in_bankruptcy=is_in_bankruptcy, is_suspended=is_suspended,
            share_capital=share_capital,
            size=enum_param(size, SIZE_MAP, "size"),
            address_type=enum_param(address_type, ADDRESS_TYPE_MAP, "address_type"),
            country=country, city=city, postal_code=postal_code, street=street,
            house_number=house_number, terc_province=terc_province,
            terc_county=terc_county, terc_municipality=terc_municipality,
            sort_by=sort_by, page=page, page_size=page_size,
        )
        return await call_api(client.get_json("org", params=params))

    @mcp.tool
    async def get_organization(id: str) -> dict:
        """Get basic data for an organization by KRS number or NIP (e.g. '12345' or 'nip1234567890')."""
        return await call_api(client.get_json(f"org/{id}"))

    @mcp.tool
    async def get_organization_krs_chapter(
        id: str,
        chapter: Annotated[
            str,
            Field(
                description=(
                    "Which KRS chapter to retrieve. One of: 'general' (name, address, registered office, "
                    "NIP/REGON, legal form, share capital, management board, proxies, shareholders, PKD "
                    "activity, OPP status, liquidation/bankruptcy data — a very broad field set), 'branches' "
                    "(organization's branches — requires Premium+), 'shares' (share/stock data), 'mentions' "
                    "(KRS mentions), 'liabilities' (requires Premium+), 'transformations' (mergers, divisions, "
                    "transformations — requires Premium+)."
                )
            ),
        ],
        entry_number: Annotated[
            int | None,
            Field(
                description=(
                    "KRS entry number to retrieve historical chapter data as of that entry, instead of the "
                    "current state."
                )
            ),
        ] = None,
    ) -> dict:
        """Get one KRS chapter (general, branches, shares, mentions, liabilities, or transformations) for an organization. 'branches', 'liabilities', and 'transformations' require a Premium+ plan."""
        polish_chapter = enum_param(chapter, CHAPTER_MAP, "chapter")
        params = {"nr_wpisu": entry_number} if entry_number is not None else {}
        return await call_api(client.get_json(f"org/{id}/krs-rozdzialy/{polish_chapter}", params=params))

    @mcp.tool
    async def get_organization_beneficial_owners(id: str) -> list:
        """Get the beneficial owners (CRBR) of an organization by KRS number or NIP. Requires a Premium+ plan."""
        return await call_api(client.get_json(f"org/{id}/crbr"))

    @mcp.tool
    async def get_organization_relations(
        id: str,
        status: Annotated[
            str,
            Field(
                description=(
                    "Whether to return current ('current', default) or historical ('historical') relations."
                )
            ),
        ] = "current",
    ) -> list:
        """Get an organization's current or historical relations with other organizations and people in the KRS."""
        polish_status = enum_param(status, RELATION_STATUS_MAP, "status")
        return await call_api(client.get_json(f"org/{id}/krs-powiazania", params={"aktualnosc": polish_status}))

    @mcp.tool
    async def get_organization_krs_extract(
        id: str,
        extract_type: Annotated[
            str,
            Field(
                description=(
                    "Which KRS extract (odpis) to download: 'current' (aktualny, requires Premium+; returns "
                    "404 for deregistered organizations) or 'full' (pelny, requires Biznes plan; still "
                    "available for deregistered organizations). The PDF reflects KRS state from within "
                    "roughly the last 30 calendar days."
                )
            ),
        ] = "current",
        return_base64: Annotated[bool, Field(description=RETURN_BASE64_DESC)] = False,
    ) -> Any:
        """Download a KRS extract (odpis) PDF for an organization. 'current' requires Premium+, 'full' requires Biznes plan. Saves the PDF to the downloads directory and returns its absolute path; pass return_base64=True to also receive the file content inline."""
        polish_type = enum_param(extract_type, EXTRACT_TYPE_MAP, "extract_type")
        content = await call_api(client.get_binary(f"org/{id}/krs-odpisy", params={"typ": polish_type}))
        return await build_pdf_tool_result(download_dir, "krs_extract", id, content, return_base64, f"krs_extract_{id}")

    @mcp.tool
    async def list_organization_krs_entries(id: str) -> list:
        """List all KRS entries (wpisy) recorded for an organization."""
        return await call_api(client.get_json(f"org/{id}/krs-wpisy"))
