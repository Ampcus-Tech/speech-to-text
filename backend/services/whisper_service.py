import re
import whisper
import numpy as np
import sounddevice as sd
import logging

logger = logging.getLogger(__name__)

model = None

def load_model():
    global model
    if model is None:
        logger.info("Loading Whisper model...")
        model = whisper.load_model("small")
        logger.info("Whisper model loaded")
    return model

def record_audio(duration=5, sample_rate=16000):
    try:
        logger.info("Recording audio...")
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        return recording.flatten()
    except Exception as e:
        logger.error(f"Audio recording error: {e}")
        return np.array([])

def listen_and_transcribe(timeout=5, sample_rate=16000):
    try:
        model = load_model()
        audio = record_audio(timeout, sample_rate)
        if audio.size == 0:
            return "", "en"
            
        result = model.transcribe(audio, fp16=False)
        logger.info(f"Whisper Recognition: {result['text']}")
        logger.info(f"Detected Language: {result['language']}")
        return result['text'], result['language']
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return "", "en"

def extract_single_field(transcript, field, language='english'):
    if not transcript:
        return ""
    
    try:
        if language != 'english':
            return transcript
        
        patterns = {
            "candidate_name": [
                r"(?:my name is|i am|name is|this is|i'm|im)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                r"^([A-Z][a-z]+\s+[A-Z][a-z]+)$",
                r"([A-Z][a-z]+ [A-Z][a-z]+)"
            ],
            "years_of_experience": [
                r"(\d+)\s*(?:years|yrs|year|y)",
                r"experience of (\d+)\s*years",
                r"(\d+)\s*\+?\s*years? exp",
                r"(\d+)\s+yoe",
                r"(\d+)\s+years of experience"
            ],
            "current_designation": [
                r"(?:i am a|my designation is|i work as|i'm a|role is|as a)\s+([a-z ]+)",
                r"^([a-z ]+)$"
            ],
            "address": [
                r"(?:i live at|my address is|address is|located at|residing at)\s+([a-z0-9, ]+)",
                r"^([a-z0-9, ]+)$"
            ],
            "email": [
                r"(?:my email is|email is|email|mail id|contact me at)\s+([\w\s@.]+)",
                r"([\w\s.]+@[\w\s.]+)"
            ]
        }
        
        for pattern in patterns.get(field, []):
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if field == "email":
                    value = re.sub(r'\b(at|at the rate|at the symbol|at sign)\b', '@', value, flags=re.IGNORECASE)
                    value = re.sub(r'\b(dot|period|full stop|point)\b', '.', value, flags=re.IGNORECASE)
                    value = re.sub(r'\s+', '', value)
                return value
        
        return transcript
    except Exception as e:
        logger.error(f"Regex error: {e}")
        return transcript