"""
Unit tests for the Cache Manager and Prompt Hashing logic.
"""

import pytest
from app.core.cache_manager import CacheManager


def test_prompt_hash_deterministic():
    """Verify that identical inputs produce the identical SHA-256 hash."""
    messages_1 = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "How do I reverse a linked list in Python?"}
    ]
    messages_2 = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "How do I reverse a linked list in Python?"}
    ]

    hash_1 = CacheManager.generate_prompt_hash("gpt-4o", messages_1, temperature=0.7)
    hash_2 = CacheManager.generate_prompt_hash("gpt-4o", messages_2, temperature=0.7)

    assert hash_1 == hash_2
    assert len(hash_1) == 64  # Standard SHA-256 length


def test_prompt_hash_distinct_for_different_params():
    """Verify that different models or temperatures produce distinct hashes."""
    messages = [{"role": "user", "content": "Tell me a joke."}]

    hash_gpt4 = CacheManager.generate_prompt_hash("gpt-4o", messages, temperature=0.5)
    hash_gemini = CacheManager.generate_prompt_hash("gemini-1.5-flash", messages, temperature=0.5)
    hash_diff_temp = CacheManager.generate_prompt_hash("gpt-4o", messages, temperature=1.0)

    assert hash_gpt4 != hash_gemini
    assert hash_gpt4 != hash_diff_temp


@pytest.mark.asyncio
async def test_in_memory_cache_cycle():
    """Verify saving and retrieving from cache manager fallback."""
    mgr = CacheManager()
    prompt_hash = "mock_hash_1234567890abcdef"
    payload = {
        "id": "chatcmpl-test",
        "choices": [{"message": {"role": "assistant", "content": "Cached reply"}}],
        "usage": {"total_tokens": 42}
    }

    # Save to cache
    await mgr.save_cached_response(prompt_hash, payload, ttl_seconds=60)

    # Retrieve
    retrieved = await mgr.get_cached_response(prompt_hash)
    assert retrieved is not None
    assert retrieved["id"] == "chatcmpl-test"
    assert retrieved["usage"]["total_tokens"] == 42
