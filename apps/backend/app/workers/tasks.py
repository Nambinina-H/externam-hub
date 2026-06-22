import logging

from app.db.session import SessionLocal

logger = logging.getLogger("worker")


def example_cleanup() -> None:
    """Exemple de tâche planifiée.

    Une tâche n'a pas de requête HTTP : elle ouvre sa propre session DB
    (pas de `Depends` ici) et la referme. Mets ta logique périodique à la place
    (purge, agrégats, rappels, synchro externe…).
    """
    db = SessionLocal()
    try:
        # ... ton travail périodique ici ...
        logger.info("Tâche planifiée 'example_cleanup' exécutée")
    finally:
        db.close()


def send_weekly_ads_reports() -> None:
    """Envoie les rapports ads hebdo aux clients dont le jour d'envoi est aujourd'hui.

    Lancée par un cron quotidien ; le filtrage par jour (0 = lundi … 6 = dimanche) est fait
    par le service. Ouvre sa propre session DB (pas de `Depends`).
    """
    from datetime import date

    from app.modules.reports.service import send_weekly_reports_for_day

    db = SessionLocal()
    try:
        today = date.today()
        count = send_weekly_reports_for_day(db, today.weekday(), today=today)
        logger.info("Rapports ads hebdo : %d client(s) traité(s) pour le jour %d", count, today.weekday())
    finally:
        db.close()
