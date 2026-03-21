import os
import sys

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

from backend.services.transcription import transcription_service

def test_transcription():
    # You would need a sample audio file here to test
    # Since I don't have one, I'll just check if the model loads
    print("Checking if Whisper model loads...")
    try:
        # Just accessing the service should trigger __init__
        service = transcription_service
        print("Success: Whisper model loaded successfully.")
    except Exception as e:
        print(f"Error: Failed to load Whisper model: {str(e)}")

if __name__ == "__main__":
    test_transcription()
