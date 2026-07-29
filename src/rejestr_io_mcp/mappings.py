"""English <-> Polish translation tables for rejestr.io API parameters and enum values."""
from __future__ import annotations

SIZE_MAP: dict[str, str] = {
    "large_medium": "duza_srednia",
    "small": "mala",
    "micro": "mikro",
    "ngo": "ngo",
}

ADDRESS_TYPE_MAP: dict[str, str] = {
    "any": "dowolny",
    "organization": "organizacja",
    "branch": "oddzial",
}

CHAPTER_MAP: dict[str, str] = {
    "general": "ogolny",
    "branches": "oddzialy",
    "shares": "akcje",
    "mentions": "wzmianki",
    "liabilities": "zobowiazania",
    "transformations": "przeksztalcenia",
}

EXTRACT_TYPE_MAP: dict[str, str] = {
    "current": "aktualny",
    "full": "pelny",
}

RELATION_STATUS_MAP: dict[str, str] = {
    "current": "aktualne",
    "historical": "historyczne",
}

DOCUMENT_FORMAT_MAP: dict[str, str] = {
    "pdf": "pdf",
    "json": "json",
}

SEARCH_ORGANIZATIONS_PARAM_MAP: dict[str, str] = {
    "name": "nazwa",
    "nip": "nip",
    "regon": "regon",
    "legal_form": "forma_prawna",
    "first_entry_date": "wpis_pierwszy_data",
    "latest_entry_date": "wpis_najnowszy_data",
    "primary_pkd_code": "przewazajacy_pkd",
    "secondary_pkd_code": "pozostaly_pkd",
    "any_pkd_code": "dowolny_pkd",
    "is_public_benefit_org": "czy_pozytku_publicznego",
    "is_deregistered": "czy_wykreslona",
    "is_in_liquidation": "czy_w_likwidacji",
    "is_in_bankruptcy": "czy_w_upadlosci",
    "is_suspended": "czy_w_zawieszeniu",
    "share_capital": "kapital",
    "size": "wielkosc",
    "address_type": "typ_adresu",
    "country": "panstwo",
    "city": "miejscowosc",
    "postal_code": "kod_pocztowy",
    "street": "ulica",
    "house_number": "nr_domu",
    "terc_province": "terc_wojewodztwo",
    "terc_county": "terc_powiat",
    "terc_municipality": "terc_gmina",
    "sort_by": "sortowanie",
    "page": "strona",
    "page_size": "ile_na_strone",
}


def translate_enum(value: str, mapping: dict[str, str], field_name: str) -> str:
    try:
        return mapping[value]
    except KeyError:
        allowed = ", ".join(sorted(mapping))
        raise ValueError(f"Invalid value {value!r} for {field_name}; expected one of: {allowed}") from None
