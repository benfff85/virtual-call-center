import logging
import os
from fastapi import FastAPI, WebSocket, Response, Request
from twilio.twiml.voice_response import VoiceResponse, Start
import json
import time
from dotenv import load_dotenv
from utilities.fastapi_utils import log_request
from utilities.logging_utils import configure_logger
from clients.twilio_rest_client import speak_on_call
# from services.vosk_transcription_service import process_audio
from services.whisper_transcription_service import WhisperTranscriptionService

logger = configure_logger('app_logger', logging.INFO)

load_dotenv()

app = FastAPI()
whisper_transcription_service = WhisperTranscriptionService(silence_duration=1.0)

@app.post("/answer")
async def answer_call(request: Request):
    logger.info("Answering call...")
    await log_request(request)
    response = VoiceResponse()
    start = Start()
    start.stream(url="wss://promptly-alert-sparrow.ngrok-free.app/ws", name="MyAudioStream")
    response.append(start)
    response.say("Speak, and I'll repeat your words.", language="en-US", voice="woman")
    response.redirect(url="/call-keepalive", method="POST")
    return Response(content=str(response), media_type="application/xml")

@app.post("/call-keepalive")
async def answer_call(request: Request):
    logger.info("Keepalive...")
    response = VoiceResponse()
    response.pause(length=15)
    response.redirect(url="/call-keepalive", method="POST")
    return Response(content=str(response), media_type="application/xml")

@app.websocket("/ws")
async def handle_audio_stream(websocket: WebSocket):
    logger.info("WebSocket connection initiated")
    await websocket.accept()
    stream_initialized = False
    call_sid = None

    try:
        last_activity = time.time()

        while True:
            try:
                data = await websocket.receive_text()
                last_activity = time.time()
                message = json.loads(data)

                if message["event"] == "connected":
                    logger.info("Twilio media stream connected")
                    continue

                if message["event"] == "start":
                    logger.info("Media stream started: %s", message["start"])
                    call_sid = message["start"]["callSid"]
                    stream_initialized = True
                    continue

                if message["event"] == "media" and stream_initialized:
                    text = whisper_transcription_service.process_audio(message["media"]["payload"])
                    if text:
                        speak_on_call(call_sid, text)

                # Close if inactive for 30 seconds
                if time.time() - last_activity > 30:
                    logger.info("Closing due to inactivity")
                    break

            except json.JSONDecodeError:
                logger.info("Received invalid JSON message")
                continue

    except Exception as e:
        logger.info("WebSocket error: %s", str(e))
    finally:
        try:
            await websocket.close()
            logger.info("WebSocket connection closed")
        except RuntimeError:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5090)