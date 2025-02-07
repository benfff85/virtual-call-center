from twilio.rest import Client
import logging
import os
from utilities.logging_utils import configure_logger
from twilio.twiml.voice_response import VoiceResponse

logger = configure_logger('twilio_rest_client_logger', logging.INFO)

def speak_on_call(call_sid: str, text_to_speak: str):
    client = Client(os.environ['TWILIO_ACCOUNT_SID'],
                    os.environ['TWILIO_AUTH_TOKEN'])

    # Create TwiML with <Say> command
    twiml = VoiceResponse()
    twiml.say(text_to_speak, voice='woman', language='en-US')
    twiml.redirect(url=f"https://{os.environ['NGROK_DOMAIN']}/call-keepalive", method="POST")
    # twiml.redirect(url="https://promptly-alert-sparrow.ngrok-free.app/call-keepalive", method="POST")

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