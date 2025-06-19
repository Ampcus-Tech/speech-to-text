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
        model = whisper.load_model("small") #larger models can be used like "base", "small", "medium", "large-v2"
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

def clean_email(text):
    if not text:
        return ""

    # Convert to lowercase and remove leading/trailing whitespace
    text = text.lower().strip()
    
    # Replace email-related phrases with symbols
    replacements = [
        (r'\b(at the rate|at the symbol|at sign)\b', '@'),
        (r'\bat\b', '@'),
        (r'\b(dot|period|full stop|point)\b', '.'),
        (r'\bunderscore\b', '_'),       
        (r'\b(dash|hyphen)\b', '-'),
        (r'\s+', ''),  # Remove all whitespace
        (r'@+', '@'),  # Replace multiple @ with single @   
              ]
    
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    
    # Remove all whitespace between words
    text = re.sub(r'\s+', '', text)
    
    # Final validation - must contain @ and .
    if '@' not in text or '.' not in text:
        return text
    
    # Capitalize first letter if it's alphabetic
    if text and text[0].isalpha():
        text = text[0].upper() + text[1:]
    
    return text


def extract_single_field(transcript, field, language='english'):
    if not transcript:
        return ""
    
    try:
        if language != 'english':
            return transcript
        
        patterns = {
            "email": [
                r"(?:my email is|email is|email|mail id|contact me at)\s+([\w\s@.]+)",
                r"([\w\s.]+@[\w\s.]+)"
            ]
        }
        
        if field == "email":
            # First try to extract using patterns
            for pattern in patterns.get(field, []):
                match = re.search(pattern, transcript, re.IGNORECASE)
                if match:
                    extracted = match.group(1).strip()
                    cleaned = clean_email(extracted)
                    if '@' in cleaned and '.' in cleaned:
                        return cleaned
            
            # If no pattern matched, try cleaning the entire transcript
            cleaned = clean_email(transcript)
            if '@' in cleaned and '.' in cleaned:
                return cleaned
            
            return transcript
        
        return transcript
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        return transcript