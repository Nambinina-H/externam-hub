"""Tâches planifiées (cron / interval) via APScheduler, en in-process.

- `BackgroundScheduler` exécute les jobs dans un pool de threads → ne bloque pas
  l'event loop, et convient au SQLAlchemy synchrone du projet.
- L'import d'APScheduler est **paresseux** (dans `_get_scheduler`) : l'app démarre
  même si la lib n'est pas installée ; elle n'est requise que si le scheduler tourne.
- Démarré/arrêté dans le lifespan de `main.py` (cf. `scheduler_enabled` dans les settings).

Attention : en **multi-process** (uvicorn `--workers N`), chaque process lancerait le scheduler →
les jobs tourneraient N fois. Dans ce cas : `SCHEDULER_ENABLED=false` sur l'API et lance
un worker séparé, ou passe à Celery Beat (avec broker).
"""

import logging

logger = logging.getLogger("scheduler")

_scheduler = None


def _get_scheduler():
    global _scheduler
    if _scheduler is None:
        from apscheduler.schedulers.background import BackgroundScheduler

        _scheduler = BackgroundScheduler()
    return _scheduler


def register_jobs(scheduler) -> None:
    """Déclare ici tes tâches planifiées."""
    from app.core.config import get_settings
    from app.workers.tasks import example_cleanup, send_weekly_ads_reports

    settings = get_settings()

    # CRON — tous les jours à 00:00
    scheduler.add_job(
        example_cleanup,
        trigger="cron",
        hour=0,
        minute=0,
        id="example_cleanup",
        replace_existing=True,
    )

    # Rapports ads hebdo — cron quotidien à `report_send_hour` ; chaque client reçoit son
    # rapport le jour qu'il a choisi (filtré dans la tâche par report_day).
    scheduler.add_job(
        send_weekly_ads_reports,
        trigger="cron",
        hour=settings.report_send_hour,
        minute=0,
        id="send_weekly_ads_reports",
        replace_existing=True,
    )


def start_scheduler() -> None:
    scheduler = _get_scheduler()
    if not scheduler.running:
        register_jobs(scheduler)
        scheduler.start()
        logger.info("Scheduler démarré (%d job(s))", len(scheduler.get_jobs()))


def stop_scheduler() -> None:
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler arrêté")
