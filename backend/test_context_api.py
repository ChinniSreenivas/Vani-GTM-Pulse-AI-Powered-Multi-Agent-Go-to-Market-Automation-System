
import os
import asyncio
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


async def main():
    api_key = os.getenv("CONTEXT_DEV_API_KEY")

    if not api_key:
        print("API key missing. Check backend/.env")
        return

    url = "https://api.context.dev/v1/web/search"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "query": "recent AI adoption trends in B2B SaaS companies in India",
        "numResults": 5,
        "markdownOptions": {"enabled": True},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            url, headers=headers, json=payload
        )

    print("HTTP status:", response.status_code)

    if response.is_success:
        data = response.json()
        for item in data.get("results", []):
            print("\nTitle:", item.get("title"))
            print("URL:", item.get("url"))
            print("Description:", item.get("description"))
    else:
        print("Request failed:", response.text[:1000])


if __name__ == "__main__":
    asyncio.run(main())
