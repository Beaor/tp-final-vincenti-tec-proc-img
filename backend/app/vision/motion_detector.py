import cv2
import numpy as np

from app.schemas import Detection


class MotionDetector:
    def detect(
        self,
        previous: np.ndarray,
        current: np.ndarray,
        sensitivity: int,
    ) -> list[Detection]:
        difference = cv2.absdiff(previous, current)
        threshold = max(12, 55 - round(sensitivity * 0.43))
        _, mask = cv2.threshold(difference, threshold, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, kernel, iterations=2)

        min_area = max(250, int(current.shape[0] * current.shape[1] * 0.002))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = []
        for contour in contours:
            if cv2.contourArea(contour) < min_area:
                continue
            x, y, width, height = cv2.boundingRect(contour)
            detections.append(
                Detection(label="Movimiento", x=x, y=y, width=width, height=height)
            )
        return detections
