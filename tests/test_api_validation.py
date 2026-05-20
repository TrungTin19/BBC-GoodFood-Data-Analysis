import pytest

import api


@pytest.fixture()
def client():
    api.app.config.update(TESTING=True)
    return api.app.test_client()


def test_recipes_rejects_invalid_page(client):
    response = client.get("/api/recipes?page=0")
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == "invalid_parameter"
    assert payload["parameter"] == "page"


def test_recipes_rejects_large_per_page(client):
    response = client.get("/api/recipes?per_page=101")
    assert response.status_code == 400
    assert response.get_json()["parameter"] == "per_page"


def test_search_rejects_empty_query(client):
    response = client.get("/api/search?q=   ")
    assert response.status_code == 400
    assert response.get_json()["parameter"] == "q"


def test_search_rejects_long_query(client):
    response = client.get("/api/search?q=" + "a" * 301)
    assert response.status_code == 400
    assert "300" in response.get_json()["message"]


def test_search_rejects_top_n_out_of_range(client):
    response = client.get("/api/search?q=chicken&top_n=999")
    assert response.status_code == 400
    assert response.get_json()["parameter"] == "top_n"


def test_search_name_rejects_invalid_top_n(client):
    response = client.get("/api/search-name?q=pasta&top_n=-1")
    assert response.status_code == 400
    assert response.get_json()["parameter"] == "top_n"
