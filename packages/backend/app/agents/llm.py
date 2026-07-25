"""llm.py — multi-provider LLM client + cost accounting.

One entry point, `complete(...)`, returns an LLMResult carrying text + token
counts + computed cost. Four providers:

- anthropic  -> native Messages API (POST /v1/messages)
- deepseek / openai / grok -> OpenAI-compatible Chat Completions

Raw HTTP via `requests` (already a Phase-1 dep) rather than four SDKs — keeps the
runtime lean (see build spec §12) and keeps one injectable seam. Tests pass a
`transport` callable so no live network is hit (see build spec §11).

Keys and base URLs come from settings (server-side only, never the browser).
Fails loudly: an auth/404/network error raises ApiError(502, "llm_provider_error").
"""

from dataclasses import dataclass

import requests

from app.config import settings
from app.errors import ApiError
from app.agents.pricing import cost_for

REQUEST_TIMEOUT = 60
ANTHROPIC_VERSION = "2023-06-01"
OPENAI_STYLE = {"deepseek", "openai", "grok"}


@dataclass
class LLMResult:
    text: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    provider: str
    model: str


def _base_url(provider: str) -> str:
    return {
        "anthropic": settings.anthropic_base_url,
        "deepseek": settings.deepseek_base_url,
        "openai": settings.openai_base_url,
        "grok": settings.grok_base_url,
    }[provider]


def _anthropic_call(model, system, messages, max_tokens, key) -> dict:
    resp = requests.post(
        f"{_base_url('anthropic')}/v1/messages",
        headers={
            "x-api-key": key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        },
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code >= 400:
        raise ApiError(502, "llm_provider_error", f"anthropic/{model}: {resp.text[:300]}")
    data = resp.json()
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    usage = data.get("usage", {})
    return {"text": text, "tokens_in": usage.get("input_tokens", 0),
            "tokens_out": usage.get("output_tokens", 0)}


def _openai_style_call(provider, model, system, messages, max_tokens, key) -> dict:
    # System prompt becomes the leading system-role message.
    msgs = ([{"role": "system", "content": system}] if system else []) + messages
    resp = requests.post(
        f"{_base_url(provider)}/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "messages": msgs, "max_tokens": max_tokens},
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code >= 400:
        raise ApiError(502, "llm_provider_error", f"{provider}/{model}: {resp.text[:300]}")
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return {"text": text, "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0)}


def _dispatch(provider, model, system, messages, max_tokens) -> dict:
    key = settings.provider_key(provider)
    if not key:
        raise ApiError(502, "llm_provider_error",
                       f"{provider}: no API key set (check the backend .env).")
    if provider == "anthropic":
        return _anthropic_call(model, system, messages, max_tokens, key)
    if provider in OPENAI_STYLE:
        return _openai_style_call(provider, model, system, messages, max_tokens, key)
    raise ApiError(502, "llm_provider_error", f"unknown provider {provider!r}")


def complete(provider: str, model: str, system: str, messages: list[dict],
             max_tokens: int = 1024, transport=None) -> LLMResult:
    """Run one completion. `transport(provider, model, system, messages, max_tokens)`
    -> {text, tokens_in, tokens_out} is injectable so tests never hit the network."""
    try:
        raw = (transport or _dispatch)(provider, model, system, messages, max_tokens)
    except ApiError:
        raise
    except requests.RequestException as e:
        raise ApiError(502, "llm_provider_error", f"{provider}/{model}: {e}")
    tokens_in = int(raw.get("tokens_in", 0) or 0)
    tokens_out = int(raw.get("tokens_out", 0) or 0)
    return LLMResult(
        text=raw.get("text", "") or "",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost_for(model, tokens_in, tokens_out),
        provider=provider,
        model=model,
    )
