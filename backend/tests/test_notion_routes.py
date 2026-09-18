from fastapi.testclient import TestClient


def test_notion_routes_require_an_owned_connection(client: TestClient) -> None:
    response = client.get("/api/v1/notion/pages/search", params={"query": "book"})

    assert response.status_code == 409
    assert response.json()["detail"]["error_code"] == "NOTION_NOT_CONNECTED"