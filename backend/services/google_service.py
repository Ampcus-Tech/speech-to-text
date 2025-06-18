'''import speech_recognition as sr
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
'''
import speech_recognition as sr
import re
import logging

logger = logging.getLogger(__name__)

def clean_email(text):
    if not text:
        return ""
    
    # Improved email cleaning with better pattern matching
    text = text.lower()
    text = re.sub(r'\s*(at|at the rate|at the symbol|at sign|@)\s*', '@', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*(dot|period|full stop|point|\.)\s*', '.', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', '', text)  # Remove all spaces
    
    # Handle common mispronunciations
    text = re.sub(r'underscore', '_', text)
    text = re.sub(r'dash|hyphen', '-', text)
    
    # Final validation
    if '@' not in text or '.' not in text:
        return text  # Return as-is if doesn't look like email
    
    return text

def listen_and_transcribe(timeout=5):
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            logger.info("Listening for Google...")
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=timeout)
        
        try:
            text = r.recognize_google(audio)
            logger.info(f"Google Recognition: {text}")
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
        # Enhanced patterns with better matching
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
        
        # If no pattern matched, return the whole transcript for some fields
        if field in ["candidate_name", "current_designation", "address", "email"]:
            if field == "email":
                return clean_email(transcript)
            return transcript
        
        return ""
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        return ""