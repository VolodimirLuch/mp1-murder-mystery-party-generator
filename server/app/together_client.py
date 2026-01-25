from __future__ import annotations

import os
from typing import Optional

import httpx


TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"


class TogetherClientError(RuntimeError):
    pass


class TogetherClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("TOGETHER_API_KEY", "")
        self.model = os.getenv("TOGETHER_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
        if not self.api_key:
            raise TogetherClientError("TOGETHER_API_KEY is not set.")

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        top_p: float = 0.8,
        max_tokens: int = 3500,
    ) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(TOGETHER_API_URL, headers=headers, json=payload)
        except httpx.RequestError as exc:
            raise TogetherClientError(f"Together API request failed: {exc}") from exc

        if response.status_code >= 400:
            raise TogetherClientError(
                f"Together API error {response.status_code}: {response.text}"
            )

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise TogetherClientError("Unexpected Together API response shape.") from exc
