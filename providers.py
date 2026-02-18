from openai import OpenAI
import config


def _create_client(provider_name: str) -> OpenAI | None:
    """Create an OpenAI-compatible client for the given provider."""
    provider = config.PROVIDERS.get(provider_name)
    if not provider or not provider["api_key"]:
        return None

    extra_headers = {}
    if provider_name == "anthropic":
        extra_headers["anthropic-version"] = "2023-06-01"

    return OpenAI(
        base_url=provider["base_url"],
        api_key=provider["api_key"],
        default_headers=extra_headers or None,
    )


def _build_fallback_order() -> list[str]:
    """Build the provider fallback order: primary first, then free providers."""
    primary = config.AI_PROVIDER
    order = [primary]
    for name in config.FREE_FALLBACK_CHAIN:
        if name not in order:
            order.append(name)
    return order


# Pre-build clients for all configured providers
_clients: dict[str, OpenAI] = {}
for _name in set([config.AI_PROVIDER] + config.FREE_FALLBACK_CHAIN):
    _client = _create_client(_name)
    if _client:
        _clients[_name] = _client

FALLBACK_ORDER = _build_fallback_order()


def get_available_providers() -> list[str]:
    """Return list of provider names that have valid API keys configured."""
    return [name for name in FALLBACK_ORDER if name in _clients]


def chat(messages: list[dict], system_prompt: str) -> tuple[str, str]:
    """Send messages to AI and return (response_text, provider_name).

    Tries the primary provider first, then falls back through free providers.
    Raises RuntimeError if all providers fail.
    """
    errors = []

    for provider_name in FALLBACK_ORDER:
        client = _clients.get(provider_name)
        if not client:
            continue

        provider = config.PROVIDERS[provider_name]
        try:
            response = client.chat.completions.create(
                model=provider["model"],
                max_tokens=config.MAX_TOKENS,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages,
                ],
            )
            text = response.choices[0].message.content
            return text, provider_name

        except Exception as e:
            errors.append(f"{provider['name']}: {e}")
            continue

    error_details = "\n".join(errors)
    raise RuntimeError(f"All providers failed:\n{error_details}")
