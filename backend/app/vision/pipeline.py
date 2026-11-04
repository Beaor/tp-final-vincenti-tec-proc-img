from collections import OrderedDict
from threading import Lock

import cv2
import numpy as np

from app.schemas import AnalysisOut, Detection
from app.vision.motion_detector import MotionDetector
from app.vision.object_detector import ObjectDetector


class VisionPipeline:
    max_sessions = 32

    def __init__(
        self,
        motion_detector: MotionDetector | None = None,
        object_detector: ObjectDetector | None = None,
    ) -> None:
        self.motion_detector = motion_detector or MotionDetector()
        self.object_detector = object_detector or ObjectDetector()
        self._previous_frames: OrderedDict[str, np.ndarray] = OrderedDict()
        self._lock = Lock()

    def analyze(self, session_id: str, image: np.ndarray, sensitivity: int) -> AnalysisOut:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        with self._lock:
            previous = self._previous_frames.get(session_id)
            self._previous_frames[session_id] = gray
            self._previous_frames.move_to_end(session_id)
            if len(self._previous_frames) > self.max_sessions:
                self._previous_frames.popitem(last=False)

            if previous is None or previous.shape != gray.shape:
                return AnalysisOut(motion_detected=False, detections=[])

            motion_boxes = self.motion_detector.detect(previous, gray, sensitivity)
            if not motion_boxes:
                return AnalysisOut(motion_detected=False, detections=[])

            detected_people = self.object_detector.detect_people(image)
            people = [
                person
                for person in detected_people
                if any(self._overlaps(person, motion) for motion in motion_boxes)
            ]
            detections = self._combine_detections(motion_boxes, people)
            return AnalysisOut(motion_detected=True, detections=detections)

    def reset(self, session_id: str) -> None:
        with self._lock:
            self._previous_frames.pop(session_id, None)

    @staticmethod
    def _combine_detections(
        motion_boxes: list[Detection],
        people: list[Detection],
    ) -> list[Detection]:
        result = list(people)
        for motion in motion_boxes:
            overlaps_person = any(VisionPipeline._overlaps(motion, person) for person in people)
            if not overlaps_person:
                result.append(motion)
        return result

    @staticmethod
    def _overlaps(first: Detection, second: Detection) -> bool:
        return (
            first.x < second.x + second.width
            and first.x + first.width > second.x
            and first.y < second.y + second.height
            and first.y + first.height > second.y
        )
