from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from payment_service.presentation.constants import EXCEPTION_STATUS_CODES


async def _handle(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=EXCEPTION_STATUS_CODES[type(exc)],
        content={'detail': str(exc)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    for exc_class in EXCEPTION_STATUS_CODES:
        app.add_exception_handler(exc_class, _handle)
