import logging
import os

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

from utilities.logging_utils import configure_logger

logger = configure_logger('twilio_rest_client_logger', logging.INFO)

def speak_on_call(call_sid: str, text_to_speak: str):
    """Send text to twilio for twilio tts to speak on the call"""
    client = Client(os.environ['TWILIO_ACCOUNT_SID'],
                    os.environ['TWILIO_AUTH_TOKEN'])

    # Create TwiML with <Say> command
    twiml = VoiceResponse()
    twiml.say(text_to_speak, voice='woman', language='en-US')
    twiml.redirect(url=f"https://{os.environ['NGROK_DOMAIN']}/call-keepalive", method="POST")

    try:
        # Update the live call with new TwiML instructions
        call = client.calls(call_sid).update(
            twiml=twiml.to_xml()
        )
        logger.info("Sending message to call %s message ::: %s", call.sid, text_to_speak)
        return True
    except Exception as e:
        logger.info("Error updating call: %s", str(e))
        return False

def publish_audio_to_call(call_sid: str, audio_file_location: str):
    """Send audio file callback to twilio for twilio to play on the call"""
    client = Client(os.environ['TWILIO_ACCOUNT_SID'],
                    os.environ['TWILIO_AUTH_TOKEN'])

    # Create TwiML with <Play> command
    twiml = VoiceResponse()
    twiml.play(url=audio_file_location)
    twiml.redirect(url=f"https://{os.environ['NGROK_DOMAIN']}/call-keepalive", method="POST")

    try:
        # Update the live call with new TwiML instructions
        call = client.calls(call_sid).update(
            twiml=twiml.to_xml()
        )
        logger.info(f"Sending audio to call {call.sid} file: {audio_file_location}", )
        return True
    except Exception as e:
        logger.info("Error updating call: %s", str(e))
        return False