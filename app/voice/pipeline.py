import asyncio
from dotenv import load_dotenv
load_dotenv()

from pipecat.frames.frames import Frame, TranscriptionFrame, TTSSpeakFrame, EndFrame
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.pipeline.runner import PipelineRunner
from pipecat.transports.websocket.server import WebsocketServerTransport, WebsocketServerParams
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.audio.vad.silero import SileroVADAnalyzer

from app.config import GROQ_API_KEY, DEEPGRAM_API_KEY, CARTESIA_API_KEY, CARTESIA_VOICE_ID
from app.agents.graph import run_graph
from app.logger import logger


class FrontDeskProcessor(FrameProcessor):
    """
    Bridges Pipecat voice pipeline to existing LangGraph agents.
    Receives a TranscriptionFrame (text from Deepgram),
    runs it through the same graph as /chat,
    and emits a TTSSpeakFrame (text to Cartesia).
    """

    def __init__(self, session_id: str):
        super().__init__()
        self._session_id = session_id
        # session memory lives here so multi-turn works across voice turns
        self._session_memory: dict = {}

    async def process_frame(self, frame: Frame, direction):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame) and frame.text.strip():
            user_text = frame.text.strip()
            logger.info(f"VOICE | session={self._session_id} | heard: {user_text}")

            # run_graph is the same function used by /chat
            result = run_graph(
                message=user_text,
                session_id=self._session_id,
                session_memory=self._session_memory,
            )
            self._session_memory = result.get("session_memory", self._session_memory)
            answer = result.get("answer", "I'm sorry, I didn't catch that.")
            logger.info(f"VOICE | session={self._session_id} | answer: {answer[:80]}")

            await self.push_frame(TTSSpeakFrame(text=answer))
        else:
            await self.push_frame(frame, direction)


async def run_voice_pipeline(websocket, session_id: str):
    transport = WebsocketServerTransport(
        websocket=websocket,
        params=WebsocketServerParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            add_wav_header=True,
        ),
    )

    stt = DeepgramSTTService(api_key=DEEPGRAM_API_KEY)
    tts = CartesiaTTSService(api_key=CARTESIA_API_KEY, voice_id=CARTESIA_VOICE_ID)
    frontdesk = FrontDeskProcessor(session_id=session_id)

    pipeline = Pipeline([
        transport.input(),   
        stt,               
        frontdesk,           
        tts,                 
        transport.output(),  
    ])

    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
    await PipelineRunner().run(task)