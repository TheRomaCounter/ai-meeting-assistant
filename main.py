import os
import shutil
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import database, schemas, crud, worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    yield

app = FastAPI(title="AI Meeting Assistant API", version="1.0.0", lifespan=lifespan)

# Монтируем папку со скриптами, чтобы они были доступны сайту
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_home_page():
    template_path = os.path.join("app", "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/meetings", response_model=List[schemas.MeetingResponse])
async def list_meetings(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(database.Meeting).order_by(database.Meeting.created_at.desc()))
    return result.scalars().all()

@app.post("/upload", response_model=schemas.MeetingResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(file: UploadFile = File(...), db: AsyncSession = Depends(database.get_db)):
    allowed_extensions = [".mp3", ".wav", ".m4a"]
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only MP3, WAV, and M4A are allowed."
        )

    db_meeting = await crud.create_meeting(db, filename=file.filename)
    
    os.makedirs("shared_data", exist_ok=True)
    unique_filename = f"{db_meeting.id}_{file.filename}"
    file_path = os.path.join("shared_data", unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    worker.process_meeting_audio.delay(db_meeting.id, file_path)
    
    return db_meeting

@app.get("/meetings/{meeting_id}", response_model=schemas.MeetingResponse)
async def get_meeting_status(meeting_id: int, db: AsyncSession = Depends(database.get_db)):
    meeting = await crud.get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting records not found")
    return meeting
