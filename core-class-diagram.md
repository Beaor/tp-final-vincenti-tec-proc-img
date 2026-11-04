## Arquitectura y diagrama de clases

El navegador gestiona la cámara y la interfaz. La API valida y decodifica cuadros, y delega el análisis al pipeline. Las flechas del diagrama muestran las dependencias principales y las líneas discontinuas indican los modelos que se devuelven o validan.
```mermaid
classDiagram
    class Frontend {
        +startCamera()
        +analyzeLoop()
        +drawDetections(detections)
        +addEvent(detections)
        +stopCamera()
    }

    class FastAPI {
        +health()
        +analyze_frame(file, session_id, sensitivity)
        +reset_session(session_id)
    }

    class VisionPipeline {
        +max_sessions
        +analyze(session_id, image, sensitivity) AnalysisOut
        +reset(session_id)
        -_combine_detections(motion_boxes, people)
        -_overlaps(first, second)
    }

    class MotionDetector {
        +detect(previous, current, sensitivity) list~Detection~
    }

    class ObjectDetector {
        -_hog
        +detect_people(image) list~Detection~
    }

    class AnalysisOut {
        +motion_detected: bool
        +detections: list~Detection~
    }

    class Detection {
        +label: str
        +x: int
        +y: int
        +width: int
        +height: int
    }

    Frontend --> FastAPI : envía cuadros y controla sesión
    FastAPI *-- VisionPipeline : instancia del servicio
    VisionPipeline --> MotionDetector : compara cuadros
    VisionPipeline --> ObjectDetector : busca personas
    VisionPipeline ..> AnalysisOut : construye resultado
    MotionDetector ..> Detection : genera recuadros
    ObjectDetector ..> Detection : genera recuadros
    AnalysisOut o-- Detection : contiene
```