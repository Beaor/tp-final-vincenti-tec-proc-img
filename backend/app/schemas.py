from pydantic import BaseModel


class Detection(BaseModel):
    label: str
    x: int
    y: int
    width: int
    height: int


class AnalysisOut(BaseModel):
    motion_detected: bool
    detections: list[Detection]

