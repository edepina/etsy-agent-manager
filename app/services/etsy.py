"""Etsy Open API v3 client service."""

import asyncio
import logging
from collections import Counter
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Minimum delay between API calls to respect 5 QPS limit
_MIN_DELAY = 0.25


class EtsyAPIError(Exception):
    """Raised on non-retryable Etsy API errors."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Etsy API {status_code}: {message}")


class EtsyService:
    """Etsy Open API v3 client.

    Handles search, listing retrieval, shop data, and rate limiting.
    Uses x-api-key header auth for public read endpoints (search/listings).
    OAuth bearer token required for write operations.
    """

    BASE_URL = "https://openapi.etsy.com/v3/application"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.ETSY_API_KEY
        self.shared_secret = settings.ETSY_SHARED_SECRET
        self._access_token: Optional[str] = None
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={"x-api-key": self.api_key},
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        auth_required: bool = False,
        _retry: int = 0,
    ) -> dict:
        """Internal request helper with retry and rate-limit handling."""
        headers: dict = {}
        if auth_required and self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        url = f"{self.BASE_URL}{path}"
        logger.debug("Etsy %s %s params=%s", method, url, params)

        try:
            response = await self._client.request(
                method, url, params=params, json=json, headers=headers
            )
        except httpx.TimeoutException as exc:
            raise EtsyAPIError(0, f"Request timed out: {exc}") from exc

        logger.debug("Etsy response status=%s", response.status_code)

        if response.status_code == 429:
            if _retry >= 3:
                raise EtsyAPIError(429, "Rate limit exceeded after 3 retries")
            wait = 2 ** _retry
            logger.warning("Etsy rate limit hit, waiting %ss (retry %s)", wait, _retry + 1)
            await asyncio.sleep(wait)
            return await self._request(
                method, path, params=params, json=json,
                auth_required=auth_required, _retry=_retry + 1,
            )

        if response.status_code == 403:
            raise EtsyAPIError(403, "API key unauthorised or pending approval")

        if response.status_code == 404:
            raise EtsyAPIError(404, f"Resource not found: {path}")

        if response.status_code >= 400:
            raise EtsyAPIError(response.status_code, response.text[:200])

        return response.json()

    async def search_listings(
        self,
        keywords: str,
        limit: int = 100,
        offset: int = 0,
        sort_on: str = "score",
        sort_order: str = "desc",
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> dict:
        """Search active Etsy listings.

        Returns raw API response dict with 'count' and 'results' keys.
        """
        params: dict = {
            "keywords": keywords,
            "limit": min(limit, 100),
            "offset": offset,
            "sort_on": sort_on,
            "sort_order": sort_order,
        }
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price

        await asyncio.sleep(_MIN_DELAY)
        return await self._request("GET", "/listings/active", params=params)

    async def get_listing(self, listing_id: int) -> dict:
        """Get a single listing by ID."""
        await asyncio.sleep(_MIN_DELAY)
        return await self._request("GET", f"/listings/{listing_id}")

    async def get_shop(self, shop_id: int) -> dict:
        """Get shop details."""
        await asyncio.sleep(_MIN_DELAY)
        return await self._request("GET", f"/shops/{shop_id}")

    async def get_listing_images(self, listing_id: int) -> list[dict]:
        """Get images for a listing."""
        await asyncio.sleep(_MIN_DELAY)
        data = await self._request("GET", f"/listings/{listing_id}/images")
        return data.get("results", [])

    async def get_reviews_by_listing(self, listing_id: int, limit: int = 25) -> dict:
        """Get reviews for a listing."""
        await asyncio.sleep(_MIN_DELAY)
        return await self._request(
            "GET", f"/listings/{listing_id}/reviews", params={"limit": limit}
        )

    async def search_niche(
        self,
        niche_keywords: list[str],
        max_results: int = 200,
    ) -> list[dict]:
        """Search multiple keyword variations for a niche.

        Deduplicates results by listing_id and returns a combined list
        sorted by views descending. Respects rate limits between calls.
        """
        seen: dict[int, dict] = {}
        per_keyword = max(100, max_results // len(niche_keywords))

        for keyword in niche_keywords:
            try:
                data = await self.search_listings(
                    keywords=keyword,
                    limit=min(per_keyword, 100),
                )
                for listing in data.get("results", []):
                    lid = listing.get("listing_id")
                    if lid and lid not in seen:
                        seen[lid] = listing
            except EtsyAPIError as exc:
                logger.warning("Etsy search failed for keyword '%s': %s", keyword, exc)
                continue

            if len(seen) >= max_results:
                break

        results = list(seen.values())
        results.sort(key=lambda x: x.get("views", 0), reverse=True)
        return results[:max_results]

    # ------------------------------------------------------------------ #
    # OAuth write operations (used by listing agent)                       #
    # ------------------------------------------------------------------ #

    async def get_auth_url(self, redirect_uri: str, state: str) -> str:
        """Generate Etsy OAuth2 authorisation URL."""
        return (
            f"https://www.etsy.com/oauth/connect"
            f"?response_type=code"
            f"&redirect_uri={redirect_uri}"
            f"&scope=listings_r+listings_w+transactions_r+shops_r"
            f"&client_id={self.api_key}"
            f"&state={state}"
            f"&code_challenge_method=S256"
        )

    async def exchange_code_for_token(
        self, code: str, redirect_uri: str, code_verifier: str
    ) -> dict:
        """Exchange authorisation code for access + refresh tokens."""
        response = await self._client.post(
            "https://api.etsy.com/v3/public/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": self.api_key,
                "redirect_uri": redirect_uri,
                "code": code,
                "code_verifier": code_verifier,
            },
        )
        response.raise_for_status()
        return response.json()

    async def create_draft_listing(
        self,
        shop_id: str,
        title: str,
        description: str,
        price: float,
        tags: list[str],
        quantity: int = 999,
        taxonomy_id: int = 2078,
    ) -> dict:
        """Create a new draft listing on Etsy."""
        return await self._request(
            "POST",
            f"/shops/{shop_id}/listings",
            json={
                "title": title,
                "description": description,
                "price": price,
                "quantity": quantity,
                "tags": tags[:13],
                "taxonomy_id": taxonomy_id,
                "type": "download",
                "who_made": "i_did",
                "when_made": "made_to_order",
                "is_supply": False,
            },
            auth_required=True,
        )

    async def upload_listing_image(
        self, shop_id: str, listing_id: str, image_path: str
    ) -> dict:
        """Upload a listing image/thumbnail to Etsy."""
        with open(image_path, "rb") as f:
            response = await self._client.post(
                f"{self.BASE_URL}/shops/{shop_id}/listings/{listing_id}/images",
                headers={"Authorization": f"Bearer {self._access_token}"},
                files={"image": f},
            )
            response.raise_for_status()
            return response.json()

    async def upload_digital_file(
        self, shop_id: str, listing_id: str, file_path: str
    ) -> dict:
        """Upload a digital file to an Etsy listing."""
        with open(file_path, "rb") as f:
            response = await self._client.post(
                f"{self.BASE_URL}/shops/{shop_id}/listings/{listing_id}/files",
                headers={"Authorization": f"Bearer {self._access_token}"},
                files={"file": f},
            )
            response.raise_for_status()
            return response.json()

    async def get_shop_stats(
        self, shop_id: str, start_date: str, end_date: str
    ) -> dict:
        """Retrieve shop stats for a date range."""
        return await self._request(
            "GET",
            f"/shops/{shop_id}/payment-account/ledger-entries",
            params={"min_created": start_date, "max_created": end_date, "limit": 100},
            auth_required=True,
        )

    async def update_listing(
        self, shop_id: str, listing_id: str, **kwargs
    ) -> dict:
        """Update a listing's fields."""
        return await self._request(
            "PATCH",
            f"/shops/{shop_id}/listings/{listing_id}",
            json=kwargs,
            auth_required=True,
        )


def compute_top_tags(listings: list[dict], top_n: int = 20) -> list[str]:
    """Return the most common tags across a list of Etsy listings."""
    counter: Counter = Counter()
    for listing in listings:
        for tag in listing.get("tags", []):
            counter[tag.lower().strip()] += 1
    return [tag for tag, _ in counter.most_common(top_n)]
