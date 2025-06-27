import httpx

BASE_URL = "http://127.0.0.1:3000"

def test_root():
    response = httpx.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_healthcheck():
    response = httpx.get(f"{BASE_URL}/healthcheck")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_score_all_leads():
    response = httpx.get(f"{BASE_URL}/score-all-leads")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_generate_presigned_url():
    params = {
        "filename": "test.csv",
        "content_type": "text/csv"
    }
    response = httpx.get(f"{BASE_URL}/generate-presigned-url", params=params)
    assert response.status_code == 200
    assert "url" in response.json()
