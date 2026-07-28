import asyncio
import json
import aiohttp
import websockets
from fastapi import WebSocket
from app.agents.graph import run_agent
from app.config import DEEPGRAM_API_KEY, CARTESIA_API_KEY, CARTESIA_VOICE_ID
from app.logger import logger

DEEPGRAM_URL = (
    "wss://api.deepgram.com/v1/listen"
    "?encoding=linear16&sample_rate=16000&channels=1"
    "&model=nova-2&endpointing=300&interim_results=false"
)

async def text_to_speech(text: str) -> bytes:
    url = "https://api.cartesia.ai/tts/bytes"
    headers = {
        "X-API-Key": CARTESIA_API_KEY,
        "Cartesia-Version": "2024-06-10",
        "Content-Type": "application/json",
    }
    payload = {
        "model_id": "sonic-2",
        "transcript": text,
        "voice": {"mode": "id", "id": CARTESIA_VOICE_ID},
        "output_format": {
            "container": "wav",
            "encoding": "pcm_s16le",
            "sample_rate": 16000,
        },
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                return await resp.read()
            logger.error(f"Cartesia error: {resp.status} {await resp.text()}")
            return b""

async def run_voice_pipeline(websocket: WebSocket, session_id: str):
    entities = {}
    previous_intent = ""
    transcript_queue: asyncio.Queue = asyncio.Queue()

    dg_headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}

    async with websockets.connect(DEEPGRAM_URL, additional_headers=dg_headers) as dg_ws:
        logger.info(f"VOICE | session={session_id} | Deepgram connected")

        async def receive_from_browser():
            """Forward browser audio to Deepgram."""
            try:
                while True:
                    audio = await websocket.receive_bytes()
                    await dg_ws.send(audio)
            except Exception as e:
                logger.info(f"VOICE browser disconnected: {e}")

        async def receive_from_deepgram():
            """Get transcripts from Deepgram and queue them."""
            async for msg in dg_ws:
                try:
                    data = json.loads(msg)
                    alt = data.get("channel", {}).get("alternatives", [{}])[0]
                    transcript = alt.get("transcript", "").strip()
                    is_final = data.get("is_final", False)
                    if transcript and is_final:
                        logger.info(f"VOICE STT | {session_id} | {transcript}")
                        await transcript_queue.put(transcript)
                except Exception as e:
                    logger.error(f"VOICE Deepgram parse error: {e}")

        async def process_and_respond():
            """Run transcript through agents and send TTS audio back."""
            nonlocal entities, previous_intent
            while True:
                try:
                    transcript = await asyncio.wait_for(
                        transcript_queue.get(), timeout=60
                    )
                    result = run_agent(
                        message=transcript,
                        session_id=session_id,
                        entities=entities,
                        previous_intent=previous_intent,
                    )
                    entities = result.get("entities", {})
                    previous_intent = result.get("intent", "")
                    answer = result.get("answer", "I'm sorry, I didn't catch that.")
                    logger.info(f"VOICE TTS | {session_id} | {answer[:80]}")

                    audio = await text_to_speech(answer)
                    if audio:
                        await websocket.send_bytes(audio)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"VOICE process error: {e}")
                    break

        await asyncio.gather(
            receive_from_browser(),
            receive_from_deepgram(),
            process_and_respond(),
        )