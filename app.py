import os
from dotenv import load_dotenv

load_dotenv()

AUDIO_INPUT_CHANNEL = os.getenv("AUDIO_INPUT_CHANNEL", "twilio").lower()

if AUDIO_INPUT_CHANNEL == "microphone":
    # Import and explicitly run the microphone mode
    from services.microphone_input_channel_service import run_microphone_mode
    run_microphone_mode()
else:
    # Import the Twilio/FastAPI service module to start the FastAPI app.
    # Make sure that the module (e.g., twilio_input_channel_service.py) runs its Uvicorn server
    # or exposes the FastAPI app for an external server to run.
    from services.twilio_input_channel_service import app  # app is the FastAPI instance
    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=5090)
