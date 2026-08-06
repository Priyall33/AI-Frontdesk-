import asyncio
import json
import time
import aiohttp
import websockets
from fastapi import WebSocket
from app.agents.graph import run_agent
from app.config import DEEPGRAM_API_KEY, CARTESIA_API_KEY, CARTESIA_VOICE_ID
from app.logger import logger

DEEPGRAM_URL = (
    "wss://api.deepgram.com/v1/listen"
    "?model=nova-2&encoding=linear16&sample_rate=16000&endpointing=300&interim_results=false"
)

async def text_to_speech(text: str) -> bytes:
    url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en&encoding=mp3"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"text": text}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                return await resp.read()
            logger.error(f"Deepgram TTS error: {resp.status} {await resp.text()}")
            return b""
        
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
            try:
                while True:
                    audio = await websocket.receive_bytes()
                    logger.info(f"VOICE chunk: {len(audio)} bytes")
                    await dg_ws.send(audio)
            except Exception as e:
                logger.info(f"VOICE browser disconnected: {e}")

        async def keepalive():
            try:
                while True:
                    await asyncio.sleep(8)
                    await dg_ws.send(json.dumps({"type": "KeepAlive"}))
            except Exception:
                pass

        async def receive_from_deepgram():
            async for msg in dg_ws:
                logger.info(f"VOICE DG | {msg[:200]}")
                try:
                    data = json.loads(msg)
                    alt = data.get("channel", {}).get("alternatives", [{}])[0]
                    transcript = alt.get("transcript", "").strip()
                    if transcript and data.get("is_final", False):
                        logger.info(f"VOICE STT | {session_id} | {transcript}")
                        await transcript_queue.put(transcript)
                except Exception as e:
                    logger.error(f"VOICE DG parse error: {e}")

        async def process_and_respond():
            nonlocal entities, previous_intent
            while True:
                try:
                    transcript = await asyncio.wait_for(
                        transcript_queue.get(), timeout=120
                    )
                    loop = asyncio.get_event_loop()
                    t = time.time()
                    result = await loop.run_in_executor(
                        None,
                        lambda: run_agent(
                            message=transcript,
                            session_id=session_id,
                            entities=entities,
                            previous_intent=previous_intent,
                        )
                    )
                    logger.info(f"VOICE run_agent took {time.time()-t:.2f}s")
                    entities = result.get("entities", {})
                    previous_intent = result.get("intent", "")
                    answer = result.get("answer", "I'm sorry, I didn't catch that.")
                    logger.info(f"VOICE TTS | {session_id} | {answer[:80]}")
                    t2 = time.time()
                    audio = await text_to_speech(answer)
                    logger.info(f"VOICE TTS took {time.time()-t2:.2f}s")
                    if audio:
                        await websocket.send_bytes(audio)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"VOICE process error: {e}", exc_info=True)
                    continue

        await asyncio.gather(
            receive_from_browser(),
            receive_from_deepgram(),
            process_and_respond(),
            keepalive(),
            return_exceptions=True
        )