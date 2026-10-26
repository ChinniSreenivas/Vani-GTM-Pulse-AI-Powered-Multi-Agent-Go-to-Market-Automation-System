
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

API_URL = "https://api.context.dev/v1/web/search"


async def search_web(query: str, num_results: int = 5) -> dict:
    api_key = os.getenv("CONTEXT_DEV_API_KEY")

    if not api_key:
        raise RuntimeError(
            "CONTEXT_DEV_API_KEY is missing from backend/.env"
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "query": query,
        "numResults": num_results,
        "markdownOptions": {"enabled": True},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            API_URL,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()
