"""Enregistrement automatique du journal d'audit (appelé par le middleware).

Décode l'acteur depuis le JWT (best-effort, **sans requête DB**), résout le nom de l'entité
concernée (client/utilisateur) quand c'est possible, dérive un libellé lisible, puis écrit une
ligne `AuditLog`. Tout est best-effort : une erreur d'audit ne casse jamais la requête.
"""

import logging

from app.db.session import SessionLocal
from app.modules.audit.models import AuditLog
from app.modules.auth.security import decode_token
from app.modules.clients.models import Client
from app.modules.users.models import User

logger = logging.getLogger("audit")

# Seules les actions qui MODIFIENT l'état sont journalisées (les lectures GET sont trop bruyantes).
AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

_VERBS = {"POST": "Création", "PUT": "Modification", "PATCH": "Modification", "DELETE": "Suppression"}

# Ressource (1er segment) -> nom singulier FR pour le libellé.
_RESOURCE_FR = {
    "clients": "client",
    "users": "utilisateur",
    "reports": "rapport",
    "settings": "paramètres",
    "ads": "Meta Ads",
    "audit": "journal",
}

# Action nommée en fin de chemin -> libellé FR.
_SUB_FR = {
    "send-report": "Envoi du rapport",
    "send-day": "Envoi groupé des rapports",
    "sync": "Synchronisation Meta",
    "test": "Test d'envoi email",
    "import": "Import CSV",
    "preview": "Aperçu",
    "template": "Modèle d'email",
}

# Ressources dont on sait résoudre le NOM d'après l'id du chemin : (modèle, fonction de nom).
_ENTITIES = {
    "clients": (Client, lambda c: c.name),
    "users": (User, lambda u: f"{u.firstname} {u.lastname}".strip()),
}


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


def _parse_path(path: str) -> tuple[str | None, str | None, str | None]:
    """(ressource, id, sous-action) à partir du chemin /api/<ressource>/<id?>/<sub?>."""
    segments = [s for s in path.split("/") if s and s != "api"]
    if not segments:
        return None, None, None
    resource = segments[0]
    entity_id = next((s for s in segments[1:] if s.isdigit()), None)
    last = segments[-1]
    sub = last if (len(segments) > 1 and not last.isdigit() and last != resource) else None
    return resource, entity_id, sub


def humanize(method: str, path: str, target_name: str | None = None) -> str:
    """Libellé métier : ex. « Suppression — client « William Bouzemarene » », « Envoi groupé des rapports »."""
    resource, entity_id, sub = _parse_path(path)
    if resource is None:
        return f"{method} {path}"
    type_fr = _RESOURCE_FR.get(resource, resource)
    if target_name:
        who = f"{type_fr} « {target_name} »"
    elif entity_id:
        who = f"{type_fr} #{entity_id}"
    else:
        who = type_fr
    if sub:
        label = _SUB_FR.get(sub, sub)
        return f"{label} — {who}" if (target_name or entity_id) else label
    return f"{_VERBS.get(method, method)} — {who}"


def resolve_name(path: str) -> str | None:
    """Nom de l'entité visée (best-effort) d'après le chemin ; None si inconnue/introuvable.

    À appeler AVANT la requête pour un DELETE (l'entité n'existe plus après).
    """
    resource, entity_id, _sub = _parse_path(path)
    entry = _ENTITIES.get(resource or "")
    if not entry or not entity_id:
        return None
    model, name_fn = entry
    db = SessionLocal()
    try:
        obj = db.get(model, int(entity_id))
        return name_fn(obj) if obj else None
    except Exception:
        return None
    finally:
        db.close()


def record_audit(
    method: str,
    path: str,
    status_code: int,
    request_id: str | None,
    auth_header: str | None,
    target_name: str | None = None,
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
                action=humanize(method, path, target_name),
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
