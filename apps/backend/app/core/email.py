"""Envoi d'email — interface neutre `send_email()`.

Implémentation SMTP (smtplib, stdlib). Tant que SMTP n'est pas configuré (`SMTP_USER` vide),
on **log** l'email au lieu de l'envoyer : la chaîne est testable hors-ligne / en local.
Pour passer à un service managé (Resend, SendGrid…) plus tard, il suffit de réécrire le corps
de cette fonction — les appelants ne changent pas.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.errors import EmailDeliveryError

logger = logging.getLogger("email")


def send_email(to: str | list[str], subject: str, html: str) -> None:
    # Import paresseux : la config SMTP effective vient de la base (sinon du .env).
    from app.modules.settings.service import get_effective_smtp

    cfg = get_effective_smtp()
    recipients = [to] if isinstance(to, str) else list(to)
    to_header = ", ".join(recipients)

    if not cfg.user:
        logger.info("[email:dry-run] to=%s | subject=%s (SMTP non configuré → email non envoyé)", to_header, subject)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg.from_email
    msg["To"] = to_header
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(cfg.host, cfg.port) as server:
            server.starttls()
            server.login(cfg.user, cfg.password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as exc:
        logger.error("Authentification SMTP refusée pour %s : %s", cfg.user, exc)
        raise EmailDeliveryError(
            "Authentification SMTP refusée par le serveur mail. Vérifie l'adresse d'envoi et "
            "surtout le mot de passe dans Paramètres : avec Gmail, il faut un « mot de passe "
            "d'application » (16 caractères, compte avec validation en 2 étapes) — le mot de "
            "passe habituel du compte ne fonctionne pas."
        ) from exc
    except (smtplib.SMTPException, OSError) as exc:
        logger.error("Échec de l'envoi SMTP (%s:%s) : %s", cfg.host, cfg.port, exc)
        raise EmailDeliveryError(f"Échec de l'envoi via le serveur mail ({cfg.host}) : {exc}") from exc

    logger.info("[email] envoyé à %s | subject=%s", to_header, subject)
