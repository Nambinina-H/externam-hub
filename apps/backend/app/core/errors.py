"""Exceptions métier découplées du protocole HTTP.

La couche service lève ces erreurs ; le mapping vers une réponse HTTP est fait
par le handler enregistré dans `app/core/exceptions.py`. Le métier ne dépend
donc pas de `fastapi.HTTPException`.
"""


class AppError(Exception):
    """Erreur métier de base. `status_code` est utilisé par le handler global."""

    status_code: int = 400

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class BadRequestError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class EmailDeliveryError(AppError):
    """Échec d'envoi via le fournisseur SMTP (identifiants refusés, serveur injoignable…).

    502 = la dépendance externe (serveur mail) a échoué, pas la requête du client.
    """

    status_code = 502
