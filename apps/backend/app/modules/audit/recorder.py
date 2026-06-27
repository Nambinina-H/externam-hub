"""Enregistrement automatique du journal d'audit (appelé par le middleware).

Décode l'acteur depuis le JWT (best-effort, **sans requête DB**), dérive un libellé lisible,
puis écrit une ligne `AuditLog`. Tout est best-effort : une erreur d'audit ne casse jamais
la requête de l'utilisateur.
"""

import logging

from app.db.session import SessionLocal
from app.modules.audit.models import AuditLog
from app.modules.auth.security import decode_token

logger = logging.getLogger("audit")

# Seules les actions qui MODIFIENT l'état sont journalisées (les lectures GET sont trop bruyantes).
AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

_VERBS = {"POST": "Création", "PUT": "Modification", "PATCH": "Modification", "DELETE": "Suppression"}


def is_auditable(method: str, path: str) -> bool:
    """Vrai si la requête doit être journalisée (mutation d'API, hors consultation du journal)."""
    return method in AUDITED_METHODS and path.startswith("/api/") and not path.startswith("/api/audit")


def actor_from_auth(auth_header: str | None) -> dict:
    """Acteur {id, email, role} depuis le header Authorization ; {} si absent/invalide."""
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return {}
    try:
        payload = decode_token(auth_header[7:])
        if payload.get("type") != "access":
            return {}
        return {"id": payload.get("id"), "email": payload.get("email"), "role": payload.get("role")}
    except Exception:
        return {}


def humanize(method: str, path: str) -> str:
    """Libellé court et lisible (ex. « Suppression clients », « clients — send-report »)."""
    segments = [s for s in path.split("/") if s and s != "api"]
    if not segments:
        return f"{method} {path}"
    resource = segments[0]
    last = segments[-1]
    # Action nommée en fin de chemin (non numérique) -> on la met en avant.
    if len(segments) > 1 and not last.isdigit() and last != resource:
        return f"{resource} — {last}"
    return f"{_VERBS.get(method, method)} {resource}"


def record_audit(
    method: str, path: str, status_code: int, request_id: str | None, auth_header: str | None
) -> None:
    """Écrit une ligne d'audit (best-effort : avale toute erreur pour ne pas casser la requête)."""
    actor = actor_from_auth(auth_header)
    db = SessionLocal()
    try:
        db.add(
            AuditLog(
                actor_id=actor.get("id"),
                actor_email=actor.get("email"),
                actor_role=actor.get("role"),
                method=method,
                path=path,
                action=humanize(method, path),
                status_code=status_code,
                request_id=request_id,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.warning("Audit non enregistré pour %s %s", method, path, exc_info=True)
    finally:
        db.close()
