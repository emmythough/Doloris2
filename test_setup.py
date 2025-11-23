from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    print(f"Health Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200

if __name__ == "__main__":
    try:
        test_health()
        print("Setup verification successful!")
    except Exception as e:
        print(f"Setup verification failed: {e}")
