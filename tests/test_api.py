import uuid

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.settings import get_settings

DEFAULT_TOKEN = get_settings().SECRET_KEY


@pytest.fixture()
def client(monkeypatch):
    # Stub processing to avoid heavy CPU/network in tests
    def fake_process(video_id: uuid.UUID):
        pass

    from src.api.routes import analyze as analyze_module

    monkeypatch.setattr(analyze_module, "process_video_task", fake_process)

    return TestClient(app)


def test_analyze_endpoint_accepts_file(client):
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.mp4", b"fake-binary", "video/mp4")},
        headers={"Authorization": f"Bearer {DEFAULT_TOKEN}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "task_id" in body
    assert body["status"] == "received"


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "tsos_videos_processed_total" in response.text
