import cv2
import numpy as np

from app.schemas import Detection


class ObjectDetector:
    def __init__(self) -> None:
        self._hog = cv2.HOGDescriptor()
        self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def detect_people(self, image: np.ndarray) -> list[Detection]:
        rectangles, _weights = self._hog.detectMultiScale(
            image,
            winStride=(8, 8),
            padding=(8, 8),
            scale=1.05,
        )
        return [
            Detection(
                label="Persona",
                x=int(x),
                y=int(y),
                width=int(width),
                height=int(height),
            )
            for x, y, width, height in rectangles
        ]
