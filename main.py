from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.config import CLINIC_ID, APP_ENV
from app.api.routes import router
from app.voice.pipeline import run_voice_pipeline
from app.logger import logger

app = FastAPI(
    title="AI FrontDesk",
    description="Multi-agent patient assistant with RAG and Google Calendar scheduling",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["POST", "GET"],
    allow_headers=["x-api-key", "Content-Type"],
)

app.include_router(router)

@app.get("/")
def root():
    return {"status": "ok", "service": "AI FrontDesk", "clinic_id": CLINIC_ID, "env": APP_ENV}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/voice-ui", response_class=HTMLResponse)
async def voice_ui(session_id: str = "default"):
    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>AI FrontDesk — Voice</title>
  <style>
    body {{ margin:0; background:#16A4B2; display:flex; flex-direction:column;
            align-items:center; justify-content:center; height:100vh;
            font-family:'Segoe UI',sans-serif; color:white; }}
    h2 {{ font-size:1.8rem; font-weight:300; letter-spacing:2px; margin-bottom:4px; }}
    p  {{ color:rgba(255,255,255,0.6); font-size:0.8rem; margin-bottom:2rem; }}
    #micBtn {{ padding:16px 40px; font-size:1rem; border-radius:50px;
               background:rgba(255,255,255,0.15); color:white;
               border:1px solid rgba(255,255,255,0.4); cursor:pointer; }}
    #micBtn:hover {{ background:rgba(255,255,255,0.25); }}
    #status {{ margin-top:1rem; font-size:0.85rem; color:rgba(255,255,255,0.7); }}
  </style>
</head>
<body>
  <h2>AI FRONTDESK</h2>
  <p>Voice Mode</p>
  <button id="micBtn" onclick="toggleMic()">🎤 Start Voice</button>
  <p id="status">Click to speak with Alex</p>
  <script>
  const SESSION_ID = "{session_id}";
  let ws, stream, mediaRecorder, isRecording = false;

  async function toggleMic() {{
    isRecording ? stopRecording() : await startRecording();
  }}

  async function startRecording() {{
    try {{
      ws = new WebSocket(`ws://localhost:8000/ws/voice/${{SESSION_ID}}`);
      ws.binaryType = "arraybuffer";
      ws.onopen = async () => {{
        document.getElementById("status").textContent = "🔴 Listening... speak now";
        document.getElementById("micBtn").textContent = "⏹ Stop";
        document.getElementById("micBtn").style.background = "rgba(255,100,100,0.3)";
        stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (e) => {{
          if (e.data.size > 0 && ws.readyState === WebSocket.OPEN) ws.send(e.data);
        }};
        mediaRecorder.start(250);
      }};
      ws.onmessage = async (event) => {{
        document.getElementById("status").textContent = "🔊 Alex is speaking...";
        const ctx = new AudioContext();
        const buffer = await ctx.decodeAudioData(event.data);
        const src = ctx.createBufferSource();
        src.buffer = buffer; src.connect(ctx.destination);
        src.onended = () => {{ document.getElementById("status").textContent = "🔴 Listening... speak now"; }};
        src.start();
      }};
      ws.onclose = () => resetUI();
      ws.onerror = () => {{ document.getElementById("status").textContent = "⚠️ Connection error"; resetUI(); }};
      isRecording = true;
    }} catch (err) {{
      document.getElementById("status").textContent = "Error: " + err.message;
    }}
  }}

  function stopRecording() {{
    mediaRecorder?.stop();
    stream?.getTracks().forEach(t => t.stop());
    ws?.close(); resetUI();
  }}

  function resetUI() {{
    document.getElementById("micBtn").textContent = "🎤 Start Voice";
    document.getElementById("micBtn").style.background = "rgba(255,255,255,0.15)";
    document.getElementById("status").textContent = "Click to speak with Alex";
    isRecording = false;
  }}
  </script>
</body>
</html>"""
    return html

@app.websocket("/ws/voice/{session_id}")
async def voice_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        await run_voice_pipeline(websocket, session_id)
    except Exception as e:
        logger.error(f"VOICE ERROR | session={session_id} | {e}")