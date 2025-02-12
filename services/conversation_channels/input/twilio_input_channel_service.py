import json
import logging
import os
import time

from fastapi import FastAPI, WebSocket, Request, Response, Query, HTTPException
from fastapi.responses import FileResponse
from starlette.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Start

from schemas.audio_data import AudioData
from schemas.conversation_input_channel_type import ConversationInputChannelType
from schemas.conversation_output_channel_type import ConversationOutputChannelType
from schemas.conversation_segment import ConversationSegment
from services.conversation_segment_processor_service import ConversationSegmentProcessorService
from utilities.fastapi_utils import log_request
from utilities.logging_utils import configure_logger

logger = configure_logger('twilio_input_channel_service_logger', logging.INFO)
conversation_segment_processor_service = ConversationSegmentProcessorService()

app = FastAPI()

@app.post("/answer")
async def answer_call(request: Request):
    logger.info("Answering call...")
    await log_request(request)
    response = VoiceResponse()
    start = Start()
    start.stream(url=f"wss://{os.getenv('NGROK_DOMAIN')}/ws", name="MyAudioStream")
    response.append(start)

    # Check if pre-recorded greeting in the specified voice exists, if so use it, otherwise use twilio tts to say the greeting
    prerecorded_greeting_file_name="chase-greeting-" + os.getenv('TTS_VOICE') + ".wav"
    if os.path.exists(os.getenv('AUDIO_CLIP_DIR') + "/" + prerecorded_greeting_file_name):
        response.play(url="https://" + os.getenv('NGROK_DOMAIN') + "/twilio-play?filename=" + prerecorded_greeting_file_name)
    else:
        response.say("Thank you for calling Chase. How can I help you today?")

    response.redirect(url="/call-keepalive", method="POST")
    return Response(content=str(response), media_type="application/xml")

@app.post("/call-keepalive")
async def call_keepalive(request: Request):
    response = VoiceResponse()
    response.pause(length=30)
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

                    # Instantiate a ConversationSegment object
                    conversation_segment = ConversationSegment(
                        call_id=call_sid,
                        input_audio_channel=ConversationInputChannelType.TWILIO,
                        customer_audio=AudioData(raw_audio=message["media"]["payload"], format="ULAW", frequency=8000, channels=1, bit_depth=16),
                        output_audio_channel=ConversationOutputChannelType.TWILIO
                    )

                    await conversation_segment_processor_service.process_conversation_segment(conversation_segment)

                # Close if inactive for 30 seconds
                if time.time() - last_activity > 30:
                    logger.info("Closing due to inactivity")
                    break

            except json.JSONDecodeError:
                logger.info("Received invalid JSON message")
                continue

    except WebSocketDisconnect as e:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.exception("WebSocket error:")
    finally:
        try:
            await websocket.close()
            logger.info("WebSocket connection closed")
        except RuntimeError:
            pass


@app.get("/twilio-play")
async def twilio_play(filename: str = Query(..., description="Name of the .wav file")):
    # Use os.path.basename to avoid directory traversal vulnerabilities
    safe_filename = os.path.basename(filename)

    file_path = os.path.join(os.getenv('AUDIO_CLIP_DIR'), f"{safe_filename}")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type="audio/wav")