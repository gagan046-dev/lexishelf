from fastapi.testclient import TestClient


def test_search_finds_entries_across_collections_by_term(client: TestClient) -> None:
    alchemist = client.post("/api/v1/collections", json={"name": "The Alchemist"}).json()
    mythos = client.post("/api/v1/collections", json={"name": "Mythos"}).json()
    client.post("/api/v1/vocabulary", json={"collection_id": alchemist["id"], "term": "omen"})
    client.post("/api/v1/vocabulary", json={"collection_id": mythos["id"], "term": "phenomenon"})
    client.post("/api/v1/vocabulary", json={"collection_id": mythos["id"], "term": "serendipity"})

    response = client.get("/api/v1/vocabulary/search", params={"query": "omen"})

    assert response.status_code == 200
    results = response.json()
    terms = {(item["term"], item["collection_name"]) for item in results}
    assert terms == {("omen", "The Alchemist"), ("phenomenon", "Mythos")}


def test_search_is_scoped_to_the_authenticated_user(
    client: TestClient, current_user: dict[str, str]
) -> None:
    collection = client.post("/api/v1/collections", json={"name": "Private"}).json()
    client.post("/api/v1/vocabulary", json={"collection_id": collection["id"], "term": "omen"})

    current_user["id"] = "user-b"
    response = client.get("/api/v1/vocabulary/search", params={"query": "omen"})

    assert response.status_code == 200
    assert response.json() == []
