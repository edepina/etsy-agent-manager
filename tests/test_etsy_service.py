"""Unit tests for EtsyService using httpx mock."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.etsy import EtsyService, EtsyAPIError, compute_top_tags


def _make_service() -> EtsyService:
    """Create a service with a dummy API key."""
    return EtsyService(api_key="test-key")


def _mock_response(status_code: int, json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.text = str(json_data)
    return resp


@pytest.mark.asyncio
async def test_search_listings_success():
    svc = _make_service()
    payload = {"count": 2, "results": [{"listing_id": 1}, {"listing_id": 2}]}

    with patch.object(svc._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = _mock_response(200, payload)
        result = await svc.search_listings("ramadan planner")

    assert result["count"] == 2
    assert len(result["results"]) == 2


@pytest.mark.asyncio
async def test_search_listings_empty_results():
    svc = _make_service()
    payload = {"count": 0, "results": []}

    with patch.object(svc._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = _mock_response(200, payload)
        result = await svc.search_listings("xyz niche that does not exist")

    assert result["count"] == 0
    assert result["results"] == []


@pytest.mark.asyncio
async def test_rate_limit_retries_then_succeeds():
    svc = _make_service()
    payload = {"count": 1, "results": [{"listing_id": 99}]}

    rate_limit_resp = _mock_response(429, {})
    success_resp = _mock_response(200, payload)

    with patch.object(svc._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.side_effect = [rate_limit_resp, success_resp]
        with patch("app.services.etsy.asyncio.sleep", new_callable=AsyncMock):
            result = await svc.search_listings("test")

    assert result["count"] == 1


@pytest.mark.asyncio
async def test_rate_limit_exhausted_raises():
    svc = _make_service()

    with patch.object(svc._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = _mock_response(429, {})
        with patch("app.services.etsy.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(EtsyAPIError) as exc_info:
                await svc.search_listings("test")

    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_auth_error_raises():
    svc = _make_service()

    with patch.object(svc._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = _mock_response(403, {})
        with pytest.raises(EtsyAPIError) as exc_info:
            await svc.search_listings("test")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_timeout_raises():
    svc = _make_service()

    with patch.object(svc._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.side_effect = httpx.TimeoutException("timed out")
        with pytest.raises(EtsyAPIError) as exc_info:
            await svc.search_listings("test")

    assert exc_info.value.status_code == 0


@pytest.mark.asyncio
async def test_search_niche_deduplicates():
    svc = _make_service()

    # Both keywords return overlapping listing_id 1
    def make_payload(listing_ids):
        return {"count": len(listing_ids), "results": [{"listing_id": lid, "views": lid * 10, "tags": []} for lid in listing_ids]}

    responses = [
        _mock_response(200, make_payload([1, 2, 3])),
        _mock_response(200, make_payload([1, 4, 5])),
    ]

    with patch.object(svc._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.side_effect = responses
        with patch("app.services.etsy.asyncio.sleep", new_callable=AsyncMock):
            results = await svc.search_niche(["keyword1", "keyword2"])

    listing_ids = [r["listing_id"] for r in results]
    assert len(listing_ids) == len(set(listing_ids)), "Duplicates found"
    assert set(listing_ids) == {1, 2, 3, 4, 5}


@pytest.mark.asyncio
async def test_search_niche_continues_on_keyword_failure():
    svc = _make_service()

    error_resp = _mock_response(403, {})
    ok_resp = _mock_response(200, {"count": 1, "results": [{"listing_id": 7, "views": 5, "tags": []}]})

    with patch.object(svc._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.side_effect = [error_resp, ok_resp]
        with patch("app.services.etsy.asyncio.sleep", new_callable=AsyncMock):
            results = await svc.search_niche(["bad", "good"])

    assert any(r["listing_id"] == 7 for r in results)


def test_compute_top_tags():
    listings = [
        {"tags": ["ramadan", "planner", "printable"]},
        {"tags": ["ramadan", "islamic"]},
        {"tags": ["planner", "ramadan"]},
    ]
    tags = compute_top_tags(listings, top_n=2)
    assert tags[0] == "ramadan"
    assert "planner" in tags
