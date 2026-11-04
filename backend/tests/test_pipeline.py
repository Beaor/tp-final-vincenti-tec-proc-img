import numpy as np

from app.schemas import Detection
from app.vision.pipeline import VisionPipeline


class NoPeopleDetector:
    def detect_people(self, image: np.ndarray) -> list[Detection]:
        return []


def test_first_frame_only_initializes_session() -> None:
    pipeline = VisionPipeline(object_detector=NoPeopleDetector())
    image = np.zeros((120, 160, 3), dtype=np.uint8)

    result = pipeline.analyze("test", image, sensitivity=50)

    assert result.motion_detected is False
    assert result.detections == []


def test_changed_region_is_reported_as_motion() -> None:
    pipeline = VisionPipeline(object_detector=NoPeopleDetector())
    before = np.zeros((120, 160, 3), dtype=np.uint8)
    after = before.copy()
    after[30:90, 50:110] = 255

    pipeline.analyze("test", before, sensitivity=50)
    result = pipeline.analyze("test", after, sensitivity=50)

    assert result.motion_detected is True
    assert any(detection.label == "Movimiento" for detection in result.detections)


def test_reset_requires_a_new_baseline_frame() -> None:
    pipeline = VisionPipeline(object_detector=NoPeopleDetector())
    image = np.zeros((120, 160, 3), dtype=np.uint8)
    pipeline.analyze("test", image, sensitivity=50)

    pipeline.reset("test")
    result = pipeline.analyze("test", image, sensitivity=50)

    assert result.motion_detected is False


def test_person_is_only_reported_when_it_overlaps_motion() -> None:
    class FixedMotionDetector:
        def detect(self, previous: np.ndarray, current: np.ndarray, sensitivity: int) -> list[Detection]:
            return [Detection(label="Movimiento", x=0, y=0, width=30, height=30)]

    class StationaryPersonDetector:
        def detect_people(self, image: np.ndarray) -> list[Detection]:
            return [Detection(label="Persona", x=90, y=50, width=30, height=50)]

    pipeline = VisionPipeline(
        motion_detector=FixedMotionDetector(),
        object_detector=StationaryPersonDetector(),
    )
    image = np.zeros((120, 160, 3), dtype=np.uint8)
    pipeline.analyze("test", image, sensitivity=50)

    result = pipeline.analyze("test", image, sensitivity=50)

    assert [detection.label for detection in result.detections] == ["Movimiento"]
