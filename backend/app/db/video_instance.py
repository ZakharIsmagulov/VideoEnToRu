from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import VideoInstance
from app.schemas.video_instance_out import VideoInstanceOut, VideoPageOut
from app.exceptions.DBException import (
    VideoNotFound,
    NoSessionProvided,
)
from typing import Literal


async def create_video(
        user_id: int,
        name: str,
        db: AsyncSession,
) -> VideoInstance:
    video = VideoInstance(user_id=user_id, name=name)
    db.add(video)
    return video


async def get_video_by_id(
        video_id: int,
        db: AsyncSession,
) -> VideoInstance:
    stmt = select(VideoInstance).where(VideoInstance.id == video_id)
    result = await db.execute(stmt)
    video = result.scalar_one_or_none()
    if video is None:
        raise VideoNotFound(f"Video with id {video_id} is not found")
    return video


async def get_user_videos(
        user_id: int,
        limit: int = 20,
        last_id: int | None = None,
        sub_name: str | None = None,
        status: Literal["stopped", "in_queue", "in_progress", "done", "error"] | None = None,
        return_count: bool = False,
        db: AsyncSession = None,
) -> VideoPageOut:
    if db is None:
        raise NoSessionProvided()

    stmt = (select(VideoInstance)
            .where(
                (VideoInstance.user_id == user_id) &
                (VideoInstance.id > last_id if last_id else True) &
                (VideoInstance.name.contains(sub_name) if sub_name else True) &
                (VideoInstance.status == status if status else True)
            )
            .order_by(VideoInstance.id.asc())
            .limit(limit + 1)
           )
    result = await db.scalars(stmt)
    videos = list(result.all())
    has_more = True if len(videos) > limit else False
    items = videos[:-1] if has_more else videos
    new_last_id = items[-1].id if items else None

    if not return_count:
        return VideoPageOut(
            items=[VideoInstanceOut.model_validate(v) for v in items],
            last_id=new_last_id,
            has_more=has_more,
        )

    stmt = (select(func.count(VideoInstance))
            .where(
                (VideoInstance.user_id == user_id) &
                (VideoInstance.name.contains(sub_name) if sub_name else True) &
                (VideoInstance.status == status if status else True)
            )
           )
    result = await db.execute(stmt)
    total = result.scalar_one_or_none()
    return VideoPageOut(
            items=[VideoInstanceOut.model_validate(v) for v in items],
            last_id=new_last_id,
            has_more=has_more,
            total=total,
        )


def update_video_instance(
        video: VideoInstance,
        name: str | None = None,
        status: Literal["stopped", "in_queue", "in_progress", "done", "error"] | None = None,
        db: AsyncSession = None,
) -> VideoInstance:
    if db is None:
        raise NoSessionProvided()

    if name:
        video.name = name

    if status:
        video.status = status
        match status:
            case "in_progress":
                video.start_time = func.now()
            case "done":
                video.end_time = func.now()

    db.add(video)
    return video


def delete_video_instance(
        video: VideoInstance,
        db: AsyncSession,
) -> None:
    db.delete(video)
    db.flush()
