from pathlib import Path
from fastapi import UploadFile, Depends
from fastapi.responses import FileResponse
from app.exceptions.DBException import (
        JobIdNotFound,
)
from app.exceptions.APIException import (
        NoFilenameException,
        VideotypeNotAllowed,
        VideoExtensionNotAllowed,
        CannotUploadFile,
        VideoUnprocessed,
)
from app.db.db import get_db
from app.db.models import VideoInstance
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Tuple
from app.Config import settings
from app.db.video_instance import create_video, get_video_by_id

from app.tasks.task_flags import request_stop


ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/mpeg",
    "video/webm",
}
ALLOWED_EXTENSIONS = {
    ".mp4", ".mpeg", ".mpg", ".mkv", ".webm",
}


def validate_video(
        video: UploadFile,
) -> Tuple[str, str]:
    if not video.filename:
        raise NoFilenameException

    if video.content_type not in ALLOWED_VIDEO_TYPES:
        raise VideotypeNotAllowed

    filename = video.filename
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise VideoExtensionNotAllowed

    filename = Path(filename).stem
    return filename, ext


async def save_video(
        user_id: int,
        video: UploadFile,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> VideoInstance:
    name, ext = validate_video(video)

    video_instance = await create_video(user_id=user_id, name=name, db=db)

    upload_path = settings.upload_path / Path(str(video_instance.id) + ext)
    chunk_size = 1024 * 1024
    try:
        with upload_path.open("wb") as buffer:
            while chunk := await video.read(chunk_size):
                buffer.write(chunk)
        return video_instance
    except Exception as e:
        raise CannotUploadFile(f"Cannot save file to {upload_path}: {str(e)}")
    finally:
        await video.close()


async def return_video(
        video_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    processed_filepath = settings.processed_path / Path(str(video_id) + settings.processed_ext)
    if not processed_filepath.exists():
        raise VideoUnprocessed

    video = await get_video_by_id(video_id=video_id, db=db)
    name = video.name + settings.processed_ext

    return FileResponse(
        path=processed_filepath,
        filename=name,
        media_type="video/mp4",
        content_disposition_type="attachment",
    )


async def delete_video(
        video_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    video = await get_video_by_id(video_id=video_id, db=db)

    if video.status in ["in_queue", "in_progress"]:
        if video.job_id is None:
            raise JobIdNotFound(f"Job id not found for video {video_id}")
        request_stop(video.job_id)

    upload_path = settings.upload_path / Path(video.initial_name)
    if upload_path.exists():
        upload_path.unlink()

    processed_name = Path(video.initial_name).stem + settings.processed_ext
    processed_path = settings.processed_path / Path(processed_name)
    if processed_path.exists():
        processed_path.unlink()

    await db.delete(video)
