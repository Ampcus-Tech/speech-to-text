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

def listen_and_transcribe(timeout=5, sample_rate=16000, language=None):
    """
    Transcribe audio with optional manual language selection
    
    Args:
        timeout: Recording duration in seconds
        sample_rate: Audio sample rate
        language: Language code (e.g., 'en', 'es', 'fr', 'de', 'hi', 'zh', etc.)
                 If None, Whisper will auto-detect the language
    
    Returns:
        tuple: (transcribed_text, language_used)
    """
    try:
        model = load_model()
        audio = record_audio(timeout, sample_rate)
        if audio.size == 0:
            return "", language or "en"
        
        # Transcribe with or without language specification
        if language:
            logger.info(f"Transcribing with specified language: {language}")
            result = model.transcribe(audio, fp16=False, language=language)
            logger.info(f"Whisper Recognition: {result['text']}")
            logger.info(f"Used Language: {language}")
            return result['text'], language
        else:
            logger.info("Transcribing with auto-detection")
            result = model.transcribe(audio, fp16=False)
            logger.info(f"Whisper Recognition: {result['text']}")
            logger.info(f"Detected Language: {result['language']}")
            return result['text'], result['language']
            
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return "", language or "en"

def extract_email_from_speech(transcript):
    """
    Extract email from speech transcript with better handling of spoken formats and malformed patterns
    """
    if not transcript:
        return ""
    
    # Convert to lowercase for processing
    text = transcript.lower().strip()
    logger.info(f"Processing email transcript: '{text}'")
    
    # First, try to find already properly formatted emails
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    match = re.search(email_pattern, text)
    if match:
        return match.group(0)
    
    # Handle malformed patterns like @ther@egmail.com, @john@gmail.com etc.
    # Look for patterns with multiple @ symbols or garbled text
    if '@' in text:
        # Fix common Whisper transcription errors
        processed_text = text
        
        # Fix multiple @ symbols - keep only valid ones
        # Pattern: @word@domain.com -> word@domain.com  
        processed_text = re.sub(r'^@([a-zA-Z0-9]+)@', r'\1@', processed_text)
        
        # Fix missing letters after @ (common Whisper issue)
        # @gmail.com -> user@gmail.com (if there's text before @)
        if processed_text.startswith('@') and not processed_text.startswith('@@'):
            # Look for word before @ that might be username
            preceding_word_match = re.search(r'(\w+)\s*@', text)
            if preceding_word_match:
                username = preceding_word_match.group(1)
                processed_text = re.sub(r'^@', f'{username}@', processed_text)
        
        # Handle cases like "ther@egmail.com" -> "user@gmail.com"
        # Fix common domain misspellings
        domain_fixes = {
            'egmail': 'gmail',
            'gmial': 'gmail', 
            'gmai': 'gmail',
            'yahooo': 'yahoo',
            'yahho': 'yahoo',
            'hotmial': 'hotmail',
            'hotmeil': 'hotmail',
            'outlok': 'outlook',
        }
        
        for wrong, correct in domain_fixes.items():
            processed_text = re.sub(f'@{wrong}', f'@{correct}', processed_text)
            processed_text = re.sub(f'{wrong}\.com', f'{correct}.com', processed_text)
        
        # Try to extract email from processed text
        match = re.search(email_pattern, processed_text)
        if match:
            logger.info(f"Fixed email: '{text}' -> '{match.group(0)}'")
            return match.group(0)
    
    # Handle spoken email formats
    # Replace common speech-to-text variations
    replacements = {
        r'\b(at|at the rate|at the symbol|at sign|add)\b': '@',
        r'\b(dot|period|full stop|point)\b': '.',
        r'\b(dash|hyphen|minus)\b': '-',
        r'\b(underscore|under score)\b': '_',
        r'\b(plus)\b': '+',
    }
    
    processed_text = text
    for pattern, replacement in replacements.items():
        processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)
    
    # Remove extra spaces
    processed_text = re.sub(r'\s+', '', processed_text)
    
    # Try to extract email from processed text
    match = re.search(email_pattern, processed_text)
    if match:
        logger.info(f"Extracted email via speech processing: '{match.group(0)}'")
        return match.group(0)
    
    # Last resort: try to build a valid email from parts
    if '@' in processed_text:
        # Split by @ and try to construct valid email
        parts = processed_text.split('@')
        if len(parts) >= 2:
            username = parts[0]
            domain_part = '@'.join(parts[1:])  # Join in case there were multiple @
            
            # Clean username (remove non-alphanumeric except . _ -)
            username = re.sub(r'[^a-zA-Z0-9._-]', '', username)
            
            # Clean domain and ensure it has proper format
            domain_part = re.sub(r'[^a-zA-Z0-9.-]', '', domain_part)
            
            # Add .com if no extension present
            if '.' not in domain_part:
                domain_part += '.com'
            
            potential_email = f"{username}@{domain_part}"
            
            # Validate the constructed email
            if re.match(email_pattern, potential_email):
                logger.info(f"Constructed valid email: '{potential_email}'")
                return potential_email
    
    # If no email found, return empty string
    logger.warning(f"Could not extract valid email from: '{transcript}'")
    return ""

def extract_single_field(transcript, field, language='english'):
    """
    Extract specific field from transcript based on language
    
    Args:
        transcript: The transcribed text
        field: Field to extract (email, candidate_name, years_of_experience, etc.)
        language: Language of the transcript ('english', 'spanish', 'french', etc.)
    
    Returns:
        str: Extracted field value
    """
    if not transcript:
        return ""
         
    try:
        # Handle non-English languages - return transcript as-is for now
        # You can add language-specific patterns later
        if language not in ['english', 'en']:
            logger.info(f"Non-English language detected: {language}. Returning transcript as-is.")
            return transcript
        
        # Special handling for email (works for English)
        if field == "email":
            return extract_email_from_speech(transcript)
                 
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
            ]
        }
                 
        for pattern in patterns.get(field, []):
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                return value
                 
        return transcript
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        return transcript

# Example usage functions
def get_user_input_with_language():
    """
    Example function showing how to use manual language selection
    """
    # Supported languages (common ones)
    supported_languages = {
        'english': 'en',
        'spanish': 'es', 
        'french': 'fr',
        'german': 'de',
        'italian': 'it',
        'portuguese': 'pt',
        'russian': 'ru',
        'japanese': 'ja',
        'korean': 'ko',
        'chinese': 'zh',
        'hindi': 'hi',
        'arabic': 'ar',
        'dutch': 'nl',
        'swedish': 'sv',
        'norwegian': 'no',
        'danish': 'da',
        'finnish': 'fi',
        'polish': 'pl',
        'czech': 'cs',
        'hungarian': 'hu',
        'turkish': 'tr'
    }
    
    print("Available languages:")
    for lang_name, lang_code in supported_languages.items():
        print(f"  {lang_name}: {lang_code}")
    
    # Get language choice from user
    chosen_language = input("\nEnter language code (or press Enter for auto-detection): ").strip().lower()
    
    if chosen_language and chosen_language in supported_languages.values():
        print(f"Using language: {chosen_language}")
        transcript, detected_lang = listen_and_transcribe(timeout=5, language=chosen_language)
    elif chosen_language == "":
        print("Using auto-detection")
        transcript, detected_lang = listen_and_transcribe(timeout=5)
    else:
        print(f"Unknown language code: {chosen_language}. Using auto-detection.")
        transcript, detected_lang = listen_and_transcribe(timeout=5)
    
    print(f"Transcript: {transcript}")
    print(f"Language: {detected_lang}")
    
    return transcript, detected_lang

def extract_field_with_language_choice(field_name):
    """
    Example function to extract a specific field with language choice
    """
    print(f"Recording audio for {field_name}...")
    
    # You can hardcode the language here or ask user
    language_choice = input("Enter language code (en/es/fr/de/hi/zh, or Enter for auto): ").strip()
    
    if language_choice:
        transcript, used_lang = listen_and_transcribe(timeout=5, language=language_choice)
    else:
        transcript, used_lang = listen_and_transcribe(timeout=5)
    
    # Extract the field
    extracted_value = extract_single_field(transcript, field_name, used_lang)
    
    print(f"Raw transcript: {transcript}")
    print(f"Language used: {used_lang}")
    print(f"Extracted {field_name}: {extracted_value}")
    
    return extracted_value

# Test function to help debug email extraction
def test_email_extraction():
    """Test function to validate email extraction"""
    test_cases = [
        "my email is john dot smith at gmail dot com",
        "contact me at alice at company dot org", 
        "email is bob underscore wilson at hotmail dot com",
        "john.smith@gmail.com",
        "reach me at test dot email at domain dot co dot uk",
        "my email address is user plus tag at example dot com",
        # Test malformed cases like your issue
        "@ther@egmail.com",
        "@john@gmail.com", 
        "user@egmail.com",
        "alice@gmial.com",
        "test@yahooo.com",
        "john@hotmial.com",
        "ther@egmail.com",  # This seems to be your exact case
        "@gmail.com",  # Missing username
        "username@",  # Missing domain
    ]
    
    print("Testing email extraction:")
    for test in test_cases:
        result = extract_email_from_speech(test)
        print(f"Input: '{test}'")
        print(f"Output: '{result}'")
        print("-" * 50)

# Uncomment to test
# test_email_extraction()

# Example usage:
# transcript, lang = listen_and_transcribe(language='en')  # Force English
# transcript, lang = listen_and_transcribe(language='hi')  # Force Hindi  
# transcript, lang = listen_and_transcribe(language='es')  # Force Spanish
# transcript, lang = listen_and_transcribe()              # Auto-detect