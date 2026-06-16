import pytest

from shared_core.embeddings import (
    EmbeddingCache,
    HashFallbackProvider,
    cosine_similarity,
    get_embedding_provider,
    jaccard_similarity,
    tfidf_cosine,
)


@pytest.mark.asyncio
async def test_hash_fallback_is_deterministic():
    provider = HashFallbackProvider(dimensions=64)
    a = await provider.embed("hello world")
    b = await provider.embed("hello world")
    c = await provider.embed("different text")
    assert a.vector == b.vector
    assert a.dimensions == 64
    assert a.vector != c.vector


def test_cosine_similarity_identical_and_orthogonal():
    assert abs(cosine_similarity([1.0, 0.0], [1.0, 0.0]) - 1.0) < 1e-9
    assert abs(cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-9
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_tfidf_and_jaccard():
    assert abs(tfidf_cosine("the cat sat", "the cat sat") - 1.0) < 1e-9
    assert tfidf_cosine("", "anything") == 0.0
    assert abs(jaccard_similarity("a b c", "a b c") - 1.0) < 1e-9
    assert jaccard_similarity("a b", "c d") == 0.0


def test_embedding_cache_lru_eviction():
    cache = EmbeddingCache(maxsize=2)
    cache.put("m", "one", [1.0])
    cache.put("m", "two", [2.0])
    assert cache.get("m", "one") == [1.0]  # touch "one" so "two" is LRU
    cache.put("m", "three", [3.0])  # evicts "two"
    assert cache.get("m", "two") is None
    assert cache.get("m", "one") == [1.0]
    assert cache.get("m", "three") == [3.0]


def test_get_embedding_provider_offline_returns_fallback():
    provider = get_embedding_provider(offline=True)
    assert isinstance(provider, HashFallbackProvider)
    provider_no_key = get_embedding_provider(api_key=None)
    assert isinstance(provider_no_key, HashFallbackProvider)
