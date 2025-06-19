from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from services import google_service, whisper_service, vosk_service
from database import create_record, get_all_records, update_record, get_record_by_id
import re
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/transcribe-field")
async def transcribe_field(
    service: str = Query(..., regex="^(google|whisper|vosk)$"),
    field: str = Query(..., description="Field to transcribe: candidate_name, years_of_experience, current_designation, address, email"),language=None
):
    try:
        if service == "google":
            logger.info(f"Transcribing {field} with Google")
            transcript = google_service.listen_and_transcribe()
            extracted = google_service.extract_single_field(transcript, field)
            return {"value": extracted, "transcript": transcript}
        elif service == "whisper":
            logger.info(f"Transcribing {field} with Whisper")
            transcript, detected_lang = whisper_service.listen_and_transcribe()
            extracted = whisper_service.extract_single_field(transcript, field, detected_lang)
            return {"value": extracted, "transcript": transcript}
 
        elif service == "vosk":
            logger.info(f"Transcribing {field} with Vosk (Language: {language})")
            transcript, detected_lang = vosk_service.listen_and_transcribe(language=language)
            extracted = vosk_service.extract_single_field(transcript, field, detected_lang)
            return {"value": extracted, "transcript": transcript}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-record")
async def create_user_record(request: Request):
    data = await request.json()
    try:
        record_id = create_record(data)
        return {"id": record_id, "message": "Record created successfully"}
    except Exception as e:
        logger.error(f"Error creating record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/records")
async def get_records():
    try:
        records = get_all_records()
        return records
    except Exception as e:
        logger.error(f"Error fetching records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/record/{record_id}")
async def get_record(record_id: str):
    try:
        record = get_record_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        return record
    except Exception as e:
        logger.error(f"Error fetching record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/update-record/{record_id}")
async def update_user_record(record_id: str, request: Request):
    data = await request.json()
    try:
        success = update_record(record_id, data)
        if success:
            return {"message": "Record updated successfully"}
        raise HTTPException(status_code=404, detail="Record not found")
    except Exception as e:
        logger.error(f"Error updating record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "running", "message": "Voice registration system is operational"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)