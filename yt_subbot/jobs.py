import asyncio, json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Job
from datetime import datetime, timezone

POLL_INTERVAL = 2.0
MAX_ATTEMPTS = 3

async def enqueue(session: AsyncSession, kind: str, payload: dict):
    job = Job(kind=kind, payload=json.dumps(payload), status="queued")
    session.add(job)
    await session.commit()
    return job.id

async def fetch_next_job(session: AsyncSession) -> Job | None:
    q = select(Job).where(Job.status == "queued").order_by(Job.id.asc()).limit(1)
    res = await session.execute(q)
    job = res.scalar_one_or_none()
    if job:
        job.status = "running"
        job.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(job)
    return job

async def handle_job(job: Job, session: AsyncSession):
    _ = json.loads(job.payload)
    try:
        # заглушки  на E3 заменим реальными вызовами парсера
        await asyncio.sleep(0.3)
        job.status = "done"
        job.error = None
    except Exception as e:
        job.attempts += 1
        job.status = "queued" if job.attempts < MAX_ATTEMPTS else "failed"
        job.error = str(e)
    finally:
        job.updated_at = datetime.now(timezone.utc)
        await session.commit()

async def worker(session_factory):
    while True:
        async with session_factory() as session:
            job = await fetch_next_job(session)
            if job:
                await handle_job(job, session)
            else:
                await asyncio.sleep(POLL_INTERVAL)
