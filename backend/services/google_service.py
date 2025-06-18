import speech_recognition as sr
import re
import logging

logger = logging.getLogger(__name__)

def clean_email(text):
    if not text:
        return ""

    text = text.lower()
    
    # Replace common ways people say @
    text = re.sub(r'\s*(at|at the rate|at the symbol|at sign|@)\s*', '@', text, flags=re.IGNORECASE)
    
    # Replace common ways people say .
    text = re.sub(r'\s*(dot|period|full stop|point|\.)\s*', '.', text, flags=re.IGNORECASE)
    
    # Replace underscore, dash, etc.
    text = re.sub(r'underscore', '_', text)
    text = re.sub(r'dash|hyphen', '-', text)
    
    # Remove all whitespace
    text = re.sub(r'\s+', '', text)

    return text if '@' in text and '.' in text else text

def listen_and_transcribe(timeout=5):
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            logger.info("🎙️ Listening...")
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=timeout)
        
        try:
            text = r.recognize_google(audio)
            logger.info(f"📝 Recognized: {text}")
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            raise Exception(f"Google API error: {e}")
    except Exception as e:
        logger.error(f"Audio capture error: {e}")
        return ""

def extract_email(transcript):
    if not transcript:
        return ""

    try:
        patterns = [
            r"(?:my email is|email is|email|mail id|contact me at)\s+([\w\s@.]+)",
            r"([\w\s.]+@[\w\s.]+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                raw_email = match.group(1).strip()
                cleaned_email = clean_email(raw_email)
                logger.info(f"Extracted and cleaned email: {cleaned_email}")
                return cleaned_email

        # fallback to processing the whole string
        return clean_email(transcript)
    
    except Exception as e:
        logger.error(f"Email extraction error: {e}")
        return ""
