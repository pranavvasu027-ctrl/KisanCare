from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

for i in range(35):
    response = client.get("/health")
    if response.status_code == 429:
        print(f"Rate limited on request {i+1}")
        break
else:
    print("Rate limiting did not trigger!", response.status_code, response.json())
