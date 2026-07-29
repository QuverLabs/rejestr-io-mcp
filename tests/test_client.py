"""Tests for RejestrIoClient: auth header, HTTP-status error mapping, and cache hit/miss behavior."""
import httpx
import respx

from rejestr_io_mcp.errors import ApiError, AuthError, NotFoundError, PlanRequiredError, RateLimitError

BASE_URL = "https://rejestr.io/api/v2/"


@respx.mock
async def test_get_json_sends_auth_header(rejestr_client):
    route = respx.get(f"{BASE_URL}org/12345").mock(
        return_value=httpx.Response(200, json={"id": 12345})
    )
    result = await rejestr_client.get_json("org/12345")
    await rejestr_client.aclose()
    assert result == {"id": 12345}
    assert route.calls.last.request.headers["Authorization"] == "test-key"


@respx.mock
async def test_get_json_caches_repeated_calls(rejestr_client):
    route = respx.get(f"{BASE_URL}org/12345").mock(
        return_value=httpx.Response(200, json={"id": 12345})
    )
    await rejestr_client.get_json("org/12345")
    await rejestr_client.get_json("org/12345")
    await rejestr_client.aclose()
    assert route.call_count == 1


@respx.mock
async def test_get_json_different_params_bypass_cache(rejestr_client):
    respx.get(f"{BASE_URL}org").mock(
        side_effect=[
            httpx.Response(200, json={"page": 1}),
            httpx.Response(200, json={"page": 2}),
        ]
    )
    first = await rejestr_client.get_json("org", params={"strona": 1})
    second = await rejestr_client.get_json("org", params={"strona": 2})
    await rejestr_client.aclose()
    assert first == {"page": 1}
    assert second == {"page": 2}


@respx.mock
async def test_401_raises_auth_error(rejestr_client):
    respx.get(f"{BASE_URL}org/1").mock(return_value=httpx.Response(401))
    try:
        await rejestr_client.get_json("org/1")
        assert False, "expected AuthError"
    except AuthError:
        pass
    await rejestr_client.aclose()


@respx.mock
async def test_402_raises_plan_required_error(rejestr_client):
    respx.get(f"{BASE_URL}org/1/crbr").mock(return_value=httpx.Response(402))
    try:
        await rejestr_client.get_json("org/1/crbr")
        assert False, "expected PlanRequiredError"
    except PlanRequiredError:
        pass
    await rejestr_client.aclose()


@respx.mock
async def test_404_raises_not_found_error(rejestr_client):
    respx.get(f"{BASE_URL}org/999").mock(return_value=httpx.Response(404))
    try:
        await rejestr_client.get_json("org/999")
        assert False, "expected NotFoundError"
    except NotFoundError:
        pass
    await rejestr_client.aclose()


@respx.mock
async def test_429_raises_rate_limit_error(rejestr_client):
    respx.get(f"{BASE_URL}org/1").mock(return_value=httpx.Response(429))
    try:
        await rejestr_client.get_json("org/1")
        assert False, "expected RateLimitError"
    except RateLimitError:
        pass
    await rejestr_client.aclose()


@respx.mock
async def test_500_raises_api_error(rejestr_client):
    respx.get(f"{BASE_URL}org/1").mock(return_value=httpx.Response(500, text="boom"))
    try:
        await rejestr_client.get_json("org/1")
        assert False, "expected ApiError"
    except ApiError:
        pass
    await rejestr_client.aclose()


@respx.mock
async def test_get_binary_returns_bytes_and_is_not_cached(rejestr_client):
    route = respx.get(f"{BASE_URL}org/1/krs-odpisy").mock(
        return_value=httpx.Response(
            200, content=b"%PDF-1.4 fake", headers={"content-type": "application/pdf"}
        )
    )
    first = await rejestr_client.get_binary("org/1/krs-odpisy")
    second = await rejestr_client.get_binary("org/1/krs-odpisy")
    await rejestr_client.aclose()
    assert first == b"%PDF-1.4 fake"
    assert second == b"%PDF-1.4 fake"
    assert route.call_count == 2


@respx.mock
async def test_get_binary_accepts_pdf_content_type_case_insensitively(rejestr_client):
    # RFC 9110 media types are case-insensitive, and a charset/boundary
    # parameter may follow the type.
    respx.get(f"{BASE_URL}org/1/krs-odpisy").mock(
        return_value=httpx.Response(
            200, content=b"%PDF-1.4 fake", headers={"content-type": "Application/PDF; charset=binary"}
        )
    )
    assert await rejestr_client.get_binary("org/1/krs-odpisy") == b"%PDF-1.4 fake"
    await rejestr_client.aclose()


@respx.mock
async def test_get_binary_rejects_content_type_merely_prefixed_with_pdf(rejestr_client):
    # A prefix match would let "application/pdfx-evil" through.
    respx.get(f"{BASE_URL}org/1/krs-odpisy").mock(
        return_value=httpx.Response(
            200, content=b"not a pdf", headers={"content-type": "application/pdfx-evil"}
        )
    )
    try:
        await rejestr_client.get_binary("org/1/krs-odpisy")
        assert False, "expected ApiError"
    except ApiError as exc:
        assert "application/pdfx-evil" in str(exc)
    await rejestr_client.aclose()


@respx.mock
async def test_get_binary_rejects_non_pdf_content_type(rejestr_client):
    # The rejestr.io API can answer a PDF endpoint with a JSON error body and a
    # 200-range status; writing that straight to a .pdf file would report a
    # bogus success.
    respx.get(f"{BASE_URL}org/1/krs-odpisy").mock(
        return_value=httpx.Response(
            200, json={"blad": "brak srodkow"}, headers={"content-type": "application/json"}
        )
    )
    try:
        await rejestr_client.get_binary("org/1/krs-odpisy")
        assert False, "expected ApiError"
    except ApiError as exc:
        assert "application/json" in str(exc)
        assert "brak srodkow" in str(exc)
    await rejestr_client.aclose()
