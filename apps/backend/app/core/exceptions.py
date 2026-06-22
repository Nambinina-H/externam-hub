import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.errors import AppError

logger = logging.getLogger("app")


def register_exception_handlers(app: FastAPI) -> None:
    """Gestion d'erreurs centralisée au niveau de l'app.

    Les endpoints restent en `def` (exécutés dans le threadpool de FastAPI,
    sans bloquer l'event loop).

    - AppError (exceptions métier) -> son `status_code` + `detail`.
    - HTTPException / RequestValidationError : gérées par défaut par FastAPI/Starlette.
    - ValidationError (Pydantic levée hors validation des entrées) -> 422.
    - Toute autre exception non gérée -> 500 générique + log.
    """

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled error on %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
        )
        return JSONResponse(status_code=500, content={"detail": "An internal error occurred."})
