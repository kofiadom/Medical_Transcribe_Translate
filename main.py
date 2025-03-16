from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from io import BytesIO
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
import assemblyai as aai
import threading
import asyncio
from typing import Dict, List, Optional
from dotenv import load_dotenv
import os
import openai
import elevenlabs
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

assemblyai_api_key = os.getenv("ASSEMBLY_AI_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"], 
    allow_headers=["*"],  
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# AssemblyAI configuration
aai.settings.api_key = assemblyai_api_key
openai.api_key = openai_api_key
elevenlabs.set_api_key = elevenlabs_api_key

# Global variables
active_connections: Dict[str, WebSocket] = {}
transcriber: Optional[aai.RealtimeTranscriber] = None
session_id: Optional[str] = None
transcriber_lock = threading.Lock()

# The prompt for medical transcription analysis
prompt = """
You are a medical transcription analyzer. Your task is to accurately transcribe and format real-time medical speech while preserving medical terminology, diagnoses, medications, procedures, and patient details.

Ensure precise transcription of all spoken medical terms, conditions, and treatments.
Retain correct spelling for medications, tests, and clinical terminology.
Format the transcript naturally for readability, avoiding unnecessary annotations or styling.
Differentiate speaker roles (e.g., Doctor, Patient, Nurse) if identifiable.
Preserve numerical values (e.g., dosages, vital signs, test results) without modification.
Ensure grammatical coherence while maintaining a verbatim transcript.
Exclude filler words that do not contribute to medical context.
Input: Real-time medical transcript (may include detected entities from AssemblyAI).
Output: A clean, structured transcript without additional formatting or highlighting.

Rules:

Do not return any prefacing text like "Here's the formatted transcript."
Do not add, alter, or omit medical details beyond necessary corrections. 

"""

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message_type: str, message: dict):
        for connection in self.active_connections:
            await connection.send_json({"type": message_type, **message})

manager = ConnectionManager()

# AssemblyAI callback functions
def on_open(session_opened: aai.RealtimeSessionOpened):
    global session_id
    session_id = session_opened.session_id
    logger.info(f"Session ID: {session_id}")

async def on_data(transcript: aai.RealtimeTranscript):
    try:
        if not transcript.text:
            return

        if isinstance(transcript, aai.RealtimeFinalTranscript):
            await manager.broadcast('transcript', {'text': transcript.text})
            asyncio.create_task(analyze_transcript(transcript.text))
        else:
            await manager.broadcast('partial_transcript', {'text': transcript.text})
    except Exception as e:
        logger.error(f"Error processing transcript data: {e}")

async def analyze_transcript(transcript):
    try:
        result = aai.Lemur().task(
            prompt, 
            input_text=transcript,
            final_model=aai.LemurModel.claude3_5_sonnet
        ) 

        formatted_text = result.response
        await manager.broadcast('formatted_transcript', {'text': formatted_text})
        asyncio.create_task(translate_text(formatted_text, "es"))
    except Exception as e:
        logger.error(f"Error analyzing transcript: {e}")

async def translate_text(text: str, target_language: str):
    try:
        prompt = f"""
        "Translate the following medically transcribed text into {target_language}. Ensure that medical terminology, abbreviations, and context-specific 
        phrases are accurately translated while maintaining clarity and correctness. Use precise medical language that aligns with professional 
        healthcare communication. Do not simplify or generalize technical terms. If a term has multiple possible translations, choose the one 
        most commonly used in medical practice in the target language."
        
        Text to translate: {text}"
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        translated_text = response["choices"][0]["message"]["content"]
        await manager.broadcast('translated_text', {'text': translated_text})
        
        # Generate and play audio for the translated text
        audio = elevenlabs.generate(
            text=translated_text,
            voice="Bella"  # or any voice of your choice
        )
        elevenlabs.play(audio)
        
    except Exception as e:
        logger.error(f"Error translating text: {e}")

def on_error(error: aai.RealtimeError):
    logger.error(f"An error occurred: {error}")

def on_close():
    global session_id
    session_id = None
    logger.info("Closing Session")

def transcribe_real_time(language: str):
    global transcriber  
    try:
        transcriber = aai.RealtimeTranscriber(
            sample_rate=16_000,
            on_data=lambda transcript: asyncio.create_task(on_data(transcript)),
            on_error=on_error,
            on_open=on_open,
            on_close=on_close,
            language=language  # Pass the selected language to the transcriber
        )

        transcriber.connect()

        microphone_stream = aai.extras.MicrophoneStream(sample_rate=16_000)
        transcriber.stream(microphone_stream)
    except Exception as e:
        logger.error(f"Error starting real-time transcription: {e}")

# FastAPI routes
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return HTMLResponse(content="An error occurred while rendering the page.", status_code=500)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("action") == "toggle_transcription":
                language = data.get("language", "en")
                await toggle_transcription(language)
            elif data.get("action") == "translate":
                text = data.get("text")
                language = data.get("language", "es")
                await translate_text(text, language)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")

async def toggle_transcription(language: str):
    global transcriber, session_id
    with transcriber_lock:
        try:
            if session_id:
                if transcriber:
                    logger.info("Closing transcriber session")
                    transcriber.close()
                    transcriber = None
                    session_id = None
            else:
                logger.info("Starting transcriber session")
                threading.Thread(target=transcribe_real_time, args=(language,), daemon=True).start()
        except Exception as e:
            logger.error(f"Error toggling transcription: {e}")
            
@app.post("/generate_audio")
async def generate_audio(request: Request):
    try:
        data = await request.json()
        text = data.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        audio = elevenlabs.generate(
            text=text,
            voice="Bella"  # or any voice of your choice
        )

        audio_stream = BytesIO(audio)
        return StreamingResponse(audio_stream, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        raise HTTPException(status_code=500, detail="Error generating audio")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)