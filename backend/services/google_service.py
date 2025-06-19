import speech_recognition as sr
import re
import logging

logger = logging.getLogger(__name__)

def clean_email(text):
    if not text:
        return ""

    text = text.lower().strip()
    
    # First replace multi-word patterns for @ symbol
    text = re.sub(r'\b(at the rate|at the symbol|at sign)\b', '@', text)
    text = re.sub(r'\bat\b', '@', text)  # single 'at' replacement
    
    # Then replace dot/period patterns
    text = re.sub(r'\b(dot|period|full stop|point)\b', '.', text)
    
    # Handle other special characters
    text = re.sub(r'\bunderscore\b', '_', text)
    text = re.sub(r'\b(dash|hyphen)\b', '-', text)
    
    # Remove all whitespace (including spaces around @ and .)
    text = re.sub(r'\s+', '', text)
    
    # Final cleanup to handle cases where replacements created multiple @ or .
    text = re.sub(r'@+', '@', text)
    text = re.sub(r'\.+', '.', text)

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

def extract_single_field(transcript, field):
    if not transcript:
        return ""
    
    try:
        patterns = {
            "email": [
                r"(?:my email is|email is|email|mail id|contact me at)\s+([\w\s@.]+)",
                r"([\w\s.]+@[\w\s.]+)"
            ]
        }
        
        field_patterns = patterns.get(field, [])
        for pattern in field_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                logger.info(f"Extracted {field}: {value}")
                
                if field == "email":
                    value = clean_email(value)
                    logger.info(f"Cleaned email: {value}")
                
                return value
        
        if field == "email":
            return clean_email(transcript)
        return ""
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        return ""