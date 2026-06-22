"""Configuration email : la base prend le dessus sur le `.env` (fallback)."""

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.email import send_email
from app.db.session import SessionLocal
from app.modules.settings.crypto import decrypt, encrypt
from app.modules.settings.repository import EmailSettingsRepository
from app.modules.settings.schemas import EmailSettingsPublic, EmailSettingsUpdate

logger = logging.getLogger("settings")


@dataclass
class SmtpConfig:
    host: str
    port: int
    user: str
    password: str
    from_email: str
    from_name: str = ""


def resolve_smtp(db: Session) -> SmtpConfig:
    """Config SMTP effective : la ligne en base si `smtp_user` est défini, sinon le `.env`."""
    settings = get_settings()
    row = EmailSettingsRepository(db).get()
    if row and row.smtp_user:
        password = ""
        if row.smtp_password_enc:
            try:
                password = decrypt(row.smtp_password_enc)
            except Exception:  # clé JWT changée -> illisible : on retombe sur l'env
                logger.warning("Mot de passe SMTP illisible (clé changée ?) — fallback .env")
                password = settings.smtp_password
        return SmtpConfig(
            host=row.smtp_host,
            port=row.smtp_port,
            user=row.smtp_user,
            password=password,
            from_email=row.from_email or settings.from_email,
            from_name=row.from_name or "",
        )
    return SmtpConfig(
        host=settings.smtp_host,
        port=settings.smtp_port,
        user=settings.smtp_user,
        password=settings.smtp_password,
        from_email=settings.from_email,
    )


def get_effective_smtp() -> SmtpConfig:
    """Variante sans session fournie (utilisée par `send_email`)."""
    db = SessionLocal()
    try:
        return resolve_smtp(db)
    finally:
        db.close()


def get_public(repo: EmailSettingsRepository) -> EmailSettingsPublic:
    """Vue exposable : jamais le mot de passe, juste `password_set` + la source."""
    settings = get_settings()
    row = repo.get()
    if row and row.smtp_user:
        return EmailSettingsPublic(
            smtp_host=row.smtp_host,
            smtp_port=row.smtp_port,
            smtp_user=row.smtp_user,
            from_email=row.from_email or settings.from_email,
            from_name=row.from_name or "",
            password_set=bool(row.smtp_password_enc),
            source="db",
        )
    return EmailSettingsPublic(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user or "",
        from_email=settings.from_email,
        from_name="",
        password_set=bool(settings.smtp_password),
        source="env",
    )


def update_settings(repo: EmailSettingsRepository, data: EmailSettingsUpdate) -> EmailSettingsPublic:
    fields = {
        "smtp_host": data.smtp_host,
        "smtp_port": data.smtp_port,
        "smtp_user": data.smtp_user,
        "from_email": str(data.from_email),
        "from_name": data.from_name or "",
    }
    if data.smtp_password:  # mot de passe saisi -> on le (re)chiffre
        fields["smtp_password_enc"] = encrypt(data.smtp_password)
    else:
        existing = repo.get()
        if not (existing and existing.smtp_password_enc):
            # Aucun mot de passe saisi ni déjà stocké : on récupère celui du .env s'il existe
            # (migration douce .env -> base : enregistrer ne casse pas l'envoi).
            env_password = get_settings().smtp_password
            if env_password:
                fields["smtp_password_enc"] = encrypt(env_password)
    repo.upsert(**fields)
    return get_public(repo)


def send_test_email(to: str) -> None:
    """Envoie un email de test à l'adresse fournie (config SMTP effective)."""
    html = (
        "<h2>Externam Studio Hub - email de test</h2>"
        "<p>Si tu lis ceci, la configuration SMTP fonctionne.</p>"
    )
    send_email(to, "Externam Hub - test SMTP", html)
