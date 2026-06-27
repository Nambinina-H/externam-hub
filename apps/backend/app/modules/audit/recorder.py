"""Enregistrement automatique du journal d'audit (appelé par le middleware).

Deux niveaux :
- **Universel (middleware)** : toute action mutante est journalisée (qui / quoi / quand),
  avec le nom de l'entité résolu best-effort.
- **Sémantique (diff)** : pour les entités clés (client, utilisateur), on capture l'état
  AVANT la requête puis on calcule le **diff champ par champ** après — ex. « jour d'envoi :
  Lundi → Vendredi ». Le mot de passe n'est jamais lu ni stocké.

Tout est best-effort : une erreur d'audit ne casse jamais la requête.
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
_UPDATE_METHODS = {"PATCH", "PUT"}

_VERBS = {"POST": "Création", "PUT": "Modification", "PATCH": "Modification", "DELETE": "Suppression"}
_DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

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


def _day(v):
    return _DAYS[v] if isinstance(v, int) and 0 <= v < 7 else str(v)


# Champs « diffables » par entité : (attribut, libellé FR, formatteur d'affichage).
_CLIENT_FIELDS = [
    ("name", "Nom", str),
    ("company", "Entreprise", lambda v: v or "—"),
    ("contact_name", "Contact", lambda v: v or "—"),
    ("phone", "Téléphone", lambda v: v or "—"),
    ("emails", "Emails", lambda v: ", ".join(v) if v else "—"),
    ("meta_business_id", "Portefeuille", lambda v: v or "—"),
    ("managed_campaign_ids", "Campagnes gérées", lambda v: str(len(v or []))),
    ("report_day", "Jour d'envoi", _day),
    ("is_active", "Actif", lambda v: "Oui" if v else "Non"),
]
_USER_FIELDS = [
    ("firstname", "Prénom", str),
    ("lastname", "Nom", str),
    ("email", "Email", str),
    ("role", "Rôle", str),
]

# Ressources dont on sait résoudre le NOM et le DIFF : (modèle, fonction de nom, champs).
_ENTITIES = {
    "clients": (Client, lambda c: c.name, _CLIENT_FIELDS),
    "users": (User, lambda u: f"{u.firstname} {u.lastname}".strip(), _USER_FIELDS),
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


def _safe(fmt, value):
    try:
        return fmt(value)
    except Exception:
        return str(value)


def _safe_name(name_fn, obj) -> str | None:
    try:
        return name_fn(obj)
    except Exception:
        return None


def _diff(before: dict, obj, fields) -> list[dict]:
    """Liste des changements {field, before, after} entre un snapshot et l'état actuel de l'objet."""
    changes: list[dict] = []
    for attr, label, fmt in fields:
        old = before.get(attr)
        new = getattr(obj, attr, None)
        if old != new:
            changes.append({"field": label, "before": _safe(fmt, old), "after": _safe(fmt, new)})
    return changes


def capture_before(method: str, path: str) -> dict:
    """État à capturer AVANT la requête (nom pour un DELETE ; snapshot pour une modif). {} sinon."""
    if method not in AUDITED_METHODS - {"POST"}:
        return {}
    resource, entity_id, _sub = _parse_path(path)
    entry = _ENTITIES.get(resource or "")
    if not entry or not entity_id:
        return {}
    model, name_fn, fields = entry
    db = SessionLocal()
    try:
        obj = db.get(model, int(entity_id))
        if obj is None:
            return {}
        before = {"name": _safe_name(name_fn, obj)}
        if method in _UPDATE_METHODS:
            before["snapshot"] = {attr: getattr(obj, attr, None) for attr, _l, _f in fields}
        return before
    except Exception:
        return {}
    finally:
        db.close()


def record_audit(
    method: str,
    path: str,
    status_code: int,
    request_id: str | None,
    auth_header: str | None,
    before: dict | None = None,
) -> None:
    """Écrit une ligne d'audit (best-effort). `before` = état capturé avant la requête (cf. capture_before)."""
    before = before or {}
    actor = actor_from_auth(auth_header)
    resource, entity_id, _sub = _parse_path(path)
    entry = _ENTITIES.get(resource or "")
    name = before.get("name")
    changes = None
    db = SessionLocal()
    try:
        # Pour une entité connue (hors DELETE), on relit l'état APRÈS : nom à jour + diff si modif réussie.
        if entry and entity_id and method != "DELETE":
            model, name_fn, fields = entry
            obj = db.get(model, int(entity_id))
            if obj is not None:
                name = _safe_name(name_fn, obj)
                if method in _UPDATE_METHODS and "snapshot" in before and 200 <= status_code < 300:
                    changes = _diff(before["snapshot"], obj, fields) or None
        db.add(
            AuditLog(
                actor_id=actor.get("id"),
                actor_email=actor.get("email"),
                actor_role=actor.get("role"),
                method=method,
                path=path,
                action=humanize(method, path, name),
                status_code=status_code,
                request_id=request_id,
                changes=changes,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.warning("Audit non enregistré pour %s %s", method, path, exc_info=True)
    finally:
        db.close()
