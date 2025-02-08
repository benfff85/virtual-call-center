import json
import os
import time
import logging
from fastapi import FastAPI, WebSocket, Request, Response
from twilio.twiml.voice_response import VoiceResponse, Start

from utilities.logging_utils import configure_logger
from utilities.fastapi_utils import log_request
from services.whisper_transcription_service import WhisperTranscriptionService
from clients.twilio_rest_client import speak_on_call

logger = configure_logger('twilio_input_channel_service_logger', logging.INFO)

app = FastAPI()
whisper_transcription_service = WhisperTranscriptionService(silence_duration=1.0)

@app.post("/answer")
async def answer_call(request: Request):
    logger.info("Answering call...")
    await log_request(request)
    response = VoiceResponse()
    start = Start()
    start.stream(url=f"wss://{os.getenv('NGROK_DOMAIN')}/ws", name="MyAudioStream")
    response.append(start)
    response.say("Speak, and I'll repeat your words.", language="en-US", voice="woman")
    response.redirect(url="/call-keepalive", method="POST")
    return Response(content=str(response), media_type="application/xml")

@app.post("/call-keepalive")
async def call_keepalive(request: Request):
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
    last_activity = time.time()
    try:
        while True:
            try:
                data = await websocket.receive_text()
                last_activity = time.time()
                message = json.loads(data)

                if message.get("event") == "connected":
                    logger.info("Twilio media stream connected")
                    continue

                if message.get("event") == "start":
                    logger.info("Media stream started: %s", message["start"])
                    call_sid = message["start"].get("callSid")
                    stream_initialized = True
                    continue

                if message.get("event") == "media" and stream_initialized:
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
