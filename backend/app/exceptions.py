from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


def register_exception_handlers(app):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "status": exc.status_code,
                "message": exc.detail,
                # Das Frontend liest data.detail (FastAPI-Standard); ohne dieses Feld zeigten alle
                # Ansichten nur ihre generische Ersatzmeldung statt der Meldung des Backends.
                "detail": exc.detail,
                "details": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "status": 422,
                "message": "Validation failed",
                # Lesbare Kurzfassung fuer das Frontend (liest data.detail als String)
                "detail": "Ungültige Eingabe: " + "; ".join(
                    f"{'.'.join(str(p) for p in e.get('loc', []) if p != 'body')}: {e.get('msg', '')}"
                    for e in exc.errors()[:3]
                ),
                # jsonable_encoder: Fehler aus eigenen Validatoren enthalten das ValueError-Objekt im
                # ctx, das json.dumps sonst nicht serialisieren kann (-> 500 statt 422).
                "details": jsonable_encoder(exc.errors()),
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "status": 500,
                "message": "Internal server error",
                "details": str(exc),
            },
        )
