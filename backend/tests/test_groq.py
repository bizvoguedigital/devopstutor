import asyncio
import os
from pathlib import Path

import httpx
import pytest


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@pytest.mark.asyncio
async def test_groq_api():
    _load_env_file()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        pytest.skip("GROQ_API_KEY not set")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama3-8b-8192",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10,
                },
                timeout=30.0,
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("Success! API key is working.")
                print(f"Response: {data['choices'][0]['message']['content']}")
                return True
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_groq_api())
    print(f"Test result: {result}")