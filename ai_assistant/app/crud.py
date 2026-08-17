from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import Meeting

async def create_meeting(db: AsyncSession, filename: str) -> Meeting:
    db_meeting = Meeting(filename=filename, status="processing")
    db.add(db_meeting)
    await db.commit()
    await db.refresh(db_meeting)
    return db_meeting

async def get_meeting(db: AsyncSession, meeting_id: int) -> Meeting:
    result = await db.execute(select(Meeting).filter(Meeting.id == meeting_id))
    return result.scalars().first()
