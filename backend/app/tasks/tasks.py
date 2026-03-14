from app.tasks.celery_app import celery_app
from app.tasks.task_flags import clear_stop, is_stop_requested

from app.translation.TranslationAPI import VideoTranslator

from app.exceptions.TranslationException import TranslationStopped

# TODO: Добавить синхронную сессию для записи статуса в бд
@celery_app.task(bind=True, name="app.translate_video")
def translate_video_task(job_id: str, video_name: str) -> dict:
    clear_stop(job_id)

    translator = VideoTranslator(video_name=video_name, should_stop=is_stop_requested(job_id))

    try:
        res_path = translator.run()
    except TranslationStopped as e:
        return {
            "status": "stopped",
        }

    return {
        "status": "done",
        "result_path": res_path,
    }
