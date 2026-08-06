from __future__ import annotations

import itertools

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from core.config import Settings, normalized_provider, require_llm_credentials

_key_cycles: dict[str, itertools.cycle] = {}


def _get_rotated_keys(provider: str, keys_string: str | None) -> list[str]:
    """Returns the list of keys rotated by 1 each time called (Round-Robin)."""
    if not keys_string:
        return []
    keys = [k.strip() for k in keys_string.split(",") if k.strip()]
    if not keys:
        return []

    if provider not in _key_cycles:
        _key_cycles[provider] = itertools.cycle(range(len(keys)))

    start_idx = next(_key_cycles[provider])
    return keys[start_idx:] + keys[:start_idx]


def _build_with_fallbacks(llm_class, keys: list[str], key_kwarg: str = "api_key", **kwargs):
    if not keys:
        return llm_class(**kwargs)
    llms = [llm_class(**{key_kwarg: k}, **kwargs) for k in keys]
    if len(llms) > 1:
        return llms[0].with_fallbacks(llms[1:])
    return llms[0]


def build_llm(settings: Settings, temperature: float = 0.0):
    provider = normalized_provider(settings)
    require_llm_credentials(settings)

    if provider == "gemini":
        keys = _get_rotated_keys(provider, settings.google_api_key)
        return _build_with_fallbacks(
            ChatGoogleGenerativeAI, keys, key_kwarg="google_api_key", model=settings.model_name, temperature=temperature
        )
    if provider == "openai":
        keys = _get_rotated_keys(provider, settings.openai_api_key)
        return _build_with_fallbacks(
            ChatOpenAI, keys, key_kwarg="api_key", model=settings.model_name, temperature=temperature
        )
    if provider == "anthropic":
        keys = _get_rotated_keys(provider, settings.anthropic_api_key)
        return _build_with_fallbacks(
            ChatAnthropic, keys, key_kwarg="api_key", model=settings.model_name, temperature=temperature
        )
    if provider == "openrouter":
        keys = _get_rotated_keys(provider, settings.openrouter_api_key)
        return _build_with_fallbacks(
            ChatOpenAI,
            keys,
            key_kwarg="api_key",
            model=settings.model_name,
            base_url=settings.openrouter_base_url,
            temperature=temperature,
        )
    if provider == "ollama":
        return ChatOllama(
            model=settings.model_name,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )
    if provider == "custom":
        keys = _get_rotated_keys(provider, settings.custom_llm_api_key)
        if not keys:
            keys = ["unused"]
        return _build_with_fallbacks(
            ChatOpenAI,
            keys,
            key_kwarg="api_key",
            model=settings.model_name,
            base_url=settings.custom_llm_base_url,
            temperature=temperature,
        )
    raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")
