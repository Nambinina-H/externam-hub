import uuid

from app.core.logging import request_id_var

REQUEST_ID_HEADER = b"x-request-id"


class RequestIDMiddleware:
    """Middleware ASGI : associe un identifiant à chaque requête.

    Lit l'en-tête `X-Request-ID` (ou en génère un), le met dans le contextvar
    `request_id_var` (corrélation des logs) et le renvoie dans la réponse.

    Implémenté en ASGI pur (pas BaseHTTPMiddleware) pour que le contextvar
    soit bien visible depuis les endpoints et leurs logs.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        raw = headers.get(REQUEST_ID_HEADER)
        request_id = raw.decode() if raw else uuid.uuid4().hex
        token = request_id_var.set(request_id)

        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                message["headers"].append((REQUEST_ID_HEADER, request_id.encode()))
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id_var.reset(token)
