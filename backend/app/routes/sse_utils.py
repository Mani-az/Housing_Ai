import asyncio
import json
from threading import Thread
from typing import Any, Callable

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse

from app.database.database import SessionLocal


def sse_event(event: str, data: Any) -> str:
    """Format one Server-Sent Event message."""
    encoded_data = json.dumps(
        jsonable_encoder(data),
        ensure_ascii=False,
    )

    return f"event: {event}\ndata: {encoded_data}\n\n"


def sse_response(event_generator) -> StreamingResponse:
    """Create a standard SSE response with headers that reduce proxy buffering."""
    return StreamingResponse(
        event_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def stream_db_job(
    job: Callable,
    done_message: str,
    **kwargs,
) -> StreamingResponse:
    """Run a synchronous DB job in a worker thread and stream real progress events.

    The service function may accept a progress_callback keyword argument. Whenever
    it calls that callback, the frontend receives a live SSE `stage` event.
    """

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def push(event: str, data: Any):
            loop.call_soon_threadsafe(queue.put_nowait, (event, data))

        def progress_callback(message: str, progress: int):
            push("stage", {
                "message": message,
                "progress": max(0, min(int(progress), 100)),
            })

        def worker():
            db = SessionLocal()
            try:
                result = job(
                    db=db,
                    progress_callback=progress_callback,
                    **kwargs,
                )
                push("result", result)
                push("done", {
                    "message": done_message,
                    "progress": 100,
                })
            except HTTPException as exc:
                push("error", {
                    "message": exc.detail,
                    "status_code": exc.status_code,
                })
            except ValueError as exc:
                push("error", {
                    "message": str(exc),
                    "status_code": 404,
                })
            except FileNotFoundError as exc:
                push("error", {
                    "message": str(exc),
                    "status_code": 500,
                })
            except Exception as exc:
                push("error", {
                    "message": str(exc),
                    "status_code": 500,
                })
            finally:
                db.close()

        Thread(target=worker, daemon=True).start()

        while True:
            event, data = await queue.get()
            yield sse_event(event, data)

            if event in {"done", "error"}:
                break

    return sse_response(event_generator())
