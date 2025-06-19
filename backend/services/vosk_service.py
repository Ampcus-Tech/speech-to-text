import os
import json
import logging
from vosk import Model, KaldiRecognizer
import pyaudio
 
logger = logging.getLogger(__name__)
 
# Load models for both languages
model_en = None
model_hi = None
 
def load_models():
    global model_en, model_hi
    if model_en is None:
        model_path_en = "vosk-model-en-in-0.5"
        if not os.path.exists(model_path_en):
            raise Exception(f"English model not found at {model_path_en}")
        model_en = Model(model_path_en)
       
    if model_hi is None:
        model_path_hi = "vosk-model-hi-0.22"
        if not os.path.exists(model_path_hi):
            raise Exception(f"Hindi model not found at {model_path_hi}")
        model_hi = Model(model_path_hi)
   
    return model_en, model_hi
 
def listen_and_transcribe(timeout=5, language='en'):
    try:
        model_en, model_hi = load_models()
       
        # Select model based on language
        model = model_en if language == 'en' else model_hi
        recognizer = KaldiRecognizer(model, 16000)
        recognizer.SetWords(True)
       
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
        stream.start_stream()
       
        logger.info(f"🎙️ Listening for {timeout} seconds... (Language: {language})")
       
        result = []
        for i in range(0, int(16000 / 8192 * timeout)):
            data = stream.read(8192, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result.append(recognizer.Result())
       
        stream.stop_stream()
        stream.close()
        p.terminate()
       
        final_result = json.loads(recognizer.FinalResult())
        transcript = final_result.get('text', '')
        logger.info(f"📝 Vosk Recognition: {transcript}")
       
        return transcript, language
   
    except Exception as e:
        logger.error(f"Vosk transcription error: {e}")
        return "", language
 
def extract_single_field(transcript, field, language='en'):
    if not transcript:
        return ""
   
    try:
        if language == 'hi':  # Hindi processing
            # For Hindi, we'll just return the transcript as is for now
            # You can add Hindi-specific patterns later
            return transcript
       
        # English patterns (same as other services)
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