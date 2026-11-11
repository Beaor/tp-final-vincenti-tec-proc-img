const API_URL = "";
const frameCanvas = document.createElement("canvas");
const frameContext = frameCanvas.getContext("2d", { willReadFrequently: true });
const video = document.getElementById("video");
const overlay = document.getElementById("overlay");
const overlayContext = overlay.getContext("2d");
const cameraStage = document.getElementById("cameraStage");
const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");
const sensitivityInput = document.getElementById("sensitivity");
const eventList = document.getElementById("eventList");

let stream = null;
let running = false;
let sessionId = null;
let eventCount = 0;
let lastEventAt = 0;

function setCameraStatus(active, label) {
  document.getElementById("liveIndicator").classList.toggle("is-live", active);
  document.getElementById("liveLabel").textContent = label;
  document.getElementById("cameraStat").textContent = active ? "Activa" : "Inactiva";
  document.getElementById("cameraSubtext").textContent = active ? "Analizando en este dispositivo" : "Vista previa local";
  document.getElementById("frameChip").hidden = !active;
}

function updateRangeFill() {
  const value = Number(sensitivityInput.value);
  sensitivityInput.style.background = `linear-gradient(to right, #b4ee5e 0%, #b4ee5e ${value}%, #38434b ${value}%, #38434b 100%)`;
  document.getElementById("sensitivityValue").textContent = value;
}

function drawDetections(detections) {
  overlayContext.clearRect(0, 0, overlay.width, overlay.height);
  for (const detection of detections) {
    const person = detection.label === "Persona";
    const color = person ? "#66baff" : "#b4ee5e";
    overlayContext.strokeStyle = color;
    overlayContext.lineWidth = Math.max(2, overlay.width / 400);
    overlayContext.fillStyle = color;
    overlayContext.strokeRect(detection.x, detection.y, detection.width, detection.height);

    const labelWidth = Math.max(70, overlayContext.measureText(detection.label).width + 18);
    const labelY = Math.max(0, detection.y - 23);
    overlayContext.globalAlpha = 0.94;
    overlayContext.fillRect(detection.x, labelY, labelWidth, 21);
    overlayContext.globalAlpha = 1;
    overlayContext.fillStyle = "#10151b";
    overlayContext.font = "600 12px sans-serif";
    overlayContext.fillText(detection.label, detection.x + 9, labelY + 14);
  }
}

function addEvent(detections) {
  const now = Date.now();
  if (now - lastEventAt < 4000 || detections.length === 0) return;
  lastEventAt = now;
  eventCount += 1;
  document.getElementById("eventCount").textContent = eventCount;
  document.getElementById("emptyState")?.remove();

  const person = detections.some((detection) => detection.label === "Persona");
  frameCanvas.toBlob((blob) => {
    if (!blob) return;
    const imageUrl = URL.createObjectURL(blob);
    const item = document.createElement("div");
    item.className = "event-item";
    const image = document.createElement("img");
    image.className = "event-thumb";
    image.src = imageUrl;
    image.alt = person ? "Captura de persona detectada" : "Captura de movimiento";

    const description = document.createElement("div");
    const title = document.createElement("div");
    title.className = "event-title";
    const dot = document.createElement("span");
    dot.className = `legend-dot ${person ? "person-dot" : "motion-dot"}`;
    title.append(dot, document.createTextNode(person ? "Persona detectada" : "Movimiento detectado"));
    const time = document.createElement("div");
    time.className = "event-time";
    time.textContent = new Date().toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    description.append(title, time);

    const badge = document.createElement("span");
    badge.className = `event-badge${person ? " person" : ""}`;
    badge.textContent = person ? "Persona" : "Movimiento";
    item.append(image, description, badge);
    eventList.prepend(item);
    while (eventList.querySelectorAll(".event-item").length > 8) {
      const oldest = eventList.querySelector(".event-item:last-child");
      URL.revokeObjectURL(oldest.querySelector("img").src);
      oldest.remove();
    }
  }, "image/jpeg", 0.65);
}

function showAnalysisError(message) {
  document.getElementById("liveLabel").textContent = message;
}

async function analyzeLoop() {
  while (running) {
    if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
      frameCanvas.width = video.videoWidth;
      frameCanvas.height = video.videoHeight;
      overlay.width = video.videoWidth;
      overlay.height = video.videoHeight;
      cameraStage.style.aspectRatio = `${video.videoWidth} / ${video.videoHeight}`;
      frameContext.drawImage(video, 0, 0, frameCanvas.width, frameCanvas.height);

      const blob = await new Promise((resolve) => frameCanvas.toBlob(resolve, "image/jpeg", 0.72));
      if (!blob || !running) continue;
      const formData = new FormData();
      formData.append("file", blob, "frame.jpg");
      formData.append("session_id", sessionId);
      formData.append("sensitivity", sensitivityInput.value);

      try {
        const response = await fetch(`${API_URL}/api/analyze`, { method: "POST", body: formData });
        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || "No se pudo analizar el cuadro.");
        }
        const result = await response.json();
        if (!running) return;
        document.getElementById("liveLabel").textContent = "Cámara activa";
        drawDetections(result.detections);
        const moving = result.motion_detected;
        document.getElementById("motionState").classList.toggle("is-moving", moving);
        document.getElementById("motionLabel").textContent = moving ? "Movimiento detectado" : "En espera";
        if (moving) addEvent(result.detections);
      } catch (error) {
        if (!running) return;
        showAnalysisError(`Error: ${error.message}`);
      }
    }
    await new Promise((resolve) => window.setTimeout(resolve, 500));
  }
}

async function startCamera() {
  startButton.disabled = true;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "environment" },
      audio: True,
    });
    video.srcObject = stream;
    await video.play();
    sessionId = crypto.randomUUID();
    running = true;
    cameraStage.classList.add("has-video");
    startButton.disabled = true;
    stopButton.disabled = false;
    setCameraStatus(true, "Cámara activa");
    analyzeLoop();
  } catch (error) {
    stream?.getTracks().forEach((track) => track.stop());
    stream = null;
    video.srcObject = null;
    startButton.disabled = false;
    const message = error.name === "NotAllowedError"
      ? "Permiso de cámara denegado"
      : error.name === "NotFoundError"
        ? "No se encontró una cámara"
        : "No se pudo activar la cámara";
    document.getElementById("liveLabel").textContent = message;
  }
}

function stopCamera() {
  running = false;
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }
  video.srcObject = null;
  cameraStage.classList.remove("has-video");
  cameraStage.style.aspectRatio = "4 / 3";
  overlayContext.clearRect(0, 0, overlay.width, overlay.height);
  document.getElementById("motionState").classList.remove("is-moving");
  document.getElementById("motionLabel").textContent = "En espera";
  setCameraStatus(false, "Cámara apagada");
  startButton.disabled = false;
  stopButton.disabled = true;
  if (sessionId) {
    fetch(`${API_URL}/api/sessions/${sessionId}`, { method: "DELETE" }).catch(() => {
      document.getElementById("liveLabel").textContent = "Sesión local no restablecida";
    });
    sessionId = null;
  }
}

startButton.addEventListener("click", startCamera);
stopButton.addEventListener("click", stopCamera);
sensitivityInput.addEventListener("input", updateRangeFill);
document.getElementById("clearEventsButton").addEventListener("click", () => {
  eventList.querySelectorAll(".event-item img").forEach((image) => URL.revokeObjectURL(image.src));
  eventList.querySelectorAll(".event-item").forEach((item) => item.remove());
  eventCount = 0;
  lastEventAt = 0;
  document.getElementById("eventCount").textContent = "0";
  if (!document.getElementById("emptyState")) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.id = "emptyState";
    empty.innerHTML = '<span aria-hidden="true">◷</span><div><strong>Todo tranquilo por acá</strong><small>Los eventos detectados van a aparecer en esta lista.</small></div>';
    eventList.append(empty);
  }
});

window.addEventListener("beforeunload", () => {
  stream?.getTracks().forEach((track) => track.stop());
});
updateRangeFill();
