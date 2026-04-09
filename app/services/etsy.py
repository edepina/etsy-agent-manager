from typing import Optional
import httpx
from app.config import settings


class EtsyService:
    """Etsy API v3 integration.
    
    Currently: mock implementations with correct method signatures.
    Future: full OAuth 2.0 + Etsy Open API v3 integration.
    """

    BASE_URL = "https://openapi.etsy.com/v3"

    def __init__(self):
        self.api_key = settings.ETSY_API_KEY
        self.shared_secret = settings.ETSY_SHARED_SECRET
        self._access_token: Optional[str] = None

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

    async def exchange_code_for_token(self, code: str, redirect_uri: str, code_verifier: str) -> dict:
        """Exchange authorisation code for access + refresh tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/application/shops/{shop_id}/listings",
                headers={"Authorization": f"Bearer {self._access_token}", "x-api-key": self.api_key},
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
            )
            response.raise_for_status()
            return response.json()

    async def upload_listing_image(self, shop_id: str, listing_id: str, image_path: str) -> dict:
        """Upload a listing image/thumbnail to Etsy."""
        async with httpx.AsyncClient() as client:
            with open(image_path, "rb") as f:
                response = await client.post(
                    f"{self.BASE_URL}/application/shops/{shop_id}/listings/{listing_id}/images",
                    headers={"Authorization": f"Bearer {self._access_token}", "x-api-key": self.api_key},
                    files={"image": f},
                )
                response.raise_for_status()
                return response.json()

    async def upload_digital_file(self, shop_id: str, listing_id: str, file_path: str) -> dict:
        """Upload a digital file to an Etsy listing."""
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                response = await client.post(
                    f"{self.BASE_URL}/application/shops/{shop_id}/listings/{listing_id}/files",
                    headers={"Authorization": f"Bearer {self._access_token}", "x-api-key": self.api_key},
                    files={"file": f},
                )
                response.raise_for_status()
                return response.json()

    async def get_shop_stats(self, shop_id: str, start_date: str, end_date: str) -> dict:
        """Retrieve shop stats for a date range."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/application/shops/{shop_id}/payment-account/ledger-entries",
                headers={"Authorization": f"Bearer {self._access_token}", "x-api-key": self.api_key},
                params={"min_created": start_date, "max_created": end_date, "limit": 100},
            )
            response.raise_for_status()
            return response.json()

    async def get_listing(self, listing_id: str) -> dict:
        """Retrieve a single listing by ID."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/application/listings/{listing_id}",
                headers={"x-api-key": self.api_key},
            )
            response.raise_for_status()
            return response.json()

    async def update_listing(self, shop_id: str, listing_id: str, **kwargs) -> dict:
        """Update a listing's fields."""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.BASE_URL}/application/shops/{shop_id}/listings/{listing_id}",
                headers={"Authorization": f"Bearer {self._access_token}", "x-api-key": self.api_key},
                json=kwargs,
            )
            response.raise_for_status()
            return response.json()
