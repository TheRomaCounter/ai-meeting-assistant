import asyncio
import os
from celery import Celery
from sqlalchemy.future import select
from openai import OpenAI
from app.config import settings
from app.database import async_session, Meeting

celery_app = Celery(
    "ai_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

async def process_audio_and_ai(meeting_id: int, file_path: str):
    # Если в .env нет реального ключа, вернем готовую ИИ-заглушку
    if settings.OPENAI_API_KEY == "your_real_api_key_here":
        transcript_text = "Hello team, today we are discussing our new Docker architecture. It looks solid."
        summary_text = "The team discussed the containerized infrastructure update."
    else:
        # Реальный вызов OpenAI Whisper + GPT-4o-mini
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        with open(file_path, "rb") as audio_file:
            transcript_response = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        transcript_text = transcript_response.text
        
        summary_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Create a brief summary of this meeting transcript."},
                {"role": "user", "content": transcript_text}
            ]
        )
        summary_text = summary_response.choices[0].message.content

    # Сохраняем результат в базу данных
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(Meeting).filter(Meeting.id == meeting_id))
            meeting = result.scalars().first()
            if meeting:
                meeting.status = "completed"
                meeting.transcript = transcript_text
                meeting.summary = summary_text

    # Удаляем временный файл с диска после обработки
    if os.path.exists(file_path):
        os.remove(file_path)

@celery_app.task(name="app.worker.process_meeting_audio")
def process_meeting_audio(meeting_id: int, file_path: str):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_audio_and_ai(meeting_id, file_path))
    return {"status": "success", "meeting_id": meeting_id}
