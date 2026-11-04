import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.main import app


def encode_jpeg(image: np.ndarray) -> bytes:
    success, encoded = cv2.imencode(".jpg", image)
    assert success
    return encoded.tobytes()


def test_analyze_endpoint_detects_motion_between_uploaded_frames() -> None:
    client = TestClient(app)
    session_id = "api-test"
    baseline = np.zeros((120, 160, 3), dtype=np.uint8)
    moving = baseline.copy()
    moving[30:90, 50:110] = 255

    first = client.post(
        "/api/analyze",
        data={"session_id": session_id, "sensitivity": "50"},
        files={"file": ("frame.jpg", encode_jpeg(baseline), "image/jpeg")},
    )
    second = client.post(
        "/api/analyze",
        data={"session_id": session_id, "sensitivity": "50"},
        files={"file": ("frame.jpg", encode_jpeg(moving), "image/jpeg")},
    )
    reset = client.delete(f"/api/sessions/{session_id}")

    assert first.status_code == 200
    assert first.json() == {"motion_detected": False, "detections": []}
    assert second.status_code == 200
    assert second.json()["motion_detected"] is True
    assert second.json()["detections"]
    assert reset.status_code == 204
