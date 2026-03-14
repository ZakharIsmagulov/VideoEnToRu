from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Response, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.db.models import User
from app.schemas.video_instance_out import VideoInstanceOut, VideoPageOut
from app.jwts.auth import get_current_user
from app.Config import settings
from logging import getLogger


logger = getLogger(settings.api_logger)
INTERNAL_ERROR = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Internal server error",
)


router = APIRouter(prefix="/video", tags=["video"])


@router.post("/create", response_model=VideoInstanceOut)
async def create_video(
        user: Annotated[User, Depends(get_current_user)],
        file: Annotated[UploadFile, File(...)],
        db: Annotated[AsyncSession, Depends(get_db)],
) -> VideoInstanceOut:
    pass


@router.get("/{video_id}", response_model=VideoInstanceOut)
async def get_video(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
) -> VideoInstanceOut:
    pass


@router.get("/get_page", response_model=VideoPageOut)
async def get_video_page(
        user: Annotated[User, Depends(get_current_user)],
        limit: int = 20,
        last_id: int | None = None,
        video_status: Literal["stopped", "in_queue", "in_progress", "done", "error"] | None = None,
        db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> VideoPageOut:
    pass


@router.post("/{video_id}/start", status_code=status.HTTP_204_NO_CONTENT)
async def start_processing(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    pass


@router.post("/{video_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_processing(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    pass


@router.patch("/{video_id}", response_model=VideoInstanceOut)
async def update_video(
        new_name: str,
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
) -> VideoInstanceOut:
    pass


@router.get("{video_id}/download", response_model=FileResponse)
async def download_video(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    pass


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    pass