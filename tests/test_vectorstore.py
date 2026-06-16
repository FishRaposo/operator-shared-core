import pytest

from shared_core.vectorstore import (
    InMemoryVectorStore,
    PgVectorStore,
    VectorRecord,
    get_vector_store,
)


def test_in_memory_add_count_clear():
    store = InMemoryVectorStore()
    store.add_many(
        [
            VectorRecord(id="a", vector=[1.0, 0.0], payload={"t": "a"}),
            VectorRecord(id="b", vector=[0.0, 1.0], payload={"t": "b"}),
        ]
    )
    assert store.count() == 2
    store.clear()
    assert store.count() == 0


def test_in_memory_query_ranks_by_cosine():
    store = InMemoryVectorStore()
    store.add(VectorRecord(id="x", vector=[1.0, 0.0], payload={"t": "x"}))
    store.add(VectorRecord(id="y", vector=[0.0, 1.0], payload={"t": "y"}))
    store.add(VectorRecord(id="z", vector=[0.9, 0.1], payload={"t": "z"}))

    hits = store.query([1.0, 0.0], top_k=2)
    assert len(hits) == 2
    assert hits[0].id == "x"
    assert hits[0].score >= hits[1].score
    assert hits[1].id == "z"
    assert hits[0].payload["t"] == "x"


def test_upsert_replaces_existing():
    store = InMemoryVectorStore()
    store.add(VectorRecord(id="a", vector=[1.0, 0.0]))
    store.add(VectorRecord(id="a", vector=[0.0, 1.0], payload={"v": 2}))
    assert store.count() == 1
    hit = store.query([0.0, 1.0], top_k=1)[0]
    assert hit.payload == {"v": 2}


def test_get_vector_store_offline_default():
    assert isinstance(get_vector_store(offline=True), InMemoryVectorStore)
    assert isinstance(
        get_vector_store(offline=False, db_manager=None), InMemoryVectorStore
    )


@pytest.mark.parametrize(
    "bad_table",
    [
        "vectors; DROP TABLE users",  # SQL injection attempt
        "1vectors",  # cannot start with a digit
        "my-table",  # hyphen is not a valid identifier char
        "my table",  # whitespace
        "",  # empty
        "vectors)",  # stray punctuation
    ],
)
def test_pgvector_rejects_unsafe_table_name(bad_table):
    with pytest.raises(ValueError):
        PgVectorStore(object(), dimensions=8, table=bad_table)


def test_pgvector_accepts_valid_table_name():
    # Valid identifiers must still be accepted without raising.
    store = PgVectorStore(object(), dimensions=8, table="my_vectors_2")
    assert store.table == "my_vectors_2"
