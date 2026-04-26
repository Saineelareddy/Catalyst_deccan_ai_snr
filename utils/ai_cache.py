import hashlib
import json
from diskcache import Cache
from config.settings import settings

cache = Cache(settings.cache_dir)

def get_cache_key(provider: str, model: str, prompt: str, system_prompt: str | None = None) -> str:
    """
    Generates a deterministic hash for an AI request to use as a cache key.
    """
    data = {
        "provider": provider,
        "model": model,
        "prompt": prompt,
        "system_prompt": system_prompt
    }
    encoded_data = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.md5(encoded_data).hexdigest()

def get_cached_response(key: str) -> str | None:
    """Retrieves a cached response if it exists and hasn't expired."""
    return cache.get(key)

def set_cached_response(key: str, response: str):
    """Caches a response for a configured duration."""
    cache.set(key, response, expire=settings.cache_expiration_seconds)
