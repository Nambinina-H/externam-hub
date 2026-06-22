from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    environment: str = "local"

    # Port d'écoute en dev local (lu par apps/backend/run.py). Change-le si 8000 est déjà pris
    # (ex. API_PORT=8001) — aucun autre fichier à toucher. En conteneur/PaaS, le port vient
    # de la commande de lancement (Dockerfile : `--port ${PORT:-8000}`).
    api_port: int = 8000

    # --- PostgreSQL (ou DATABASE_URL direct pour Railway / base managée) ---
    postgres_user: str = "externam"
    postgres_password: str = "externam"
    postgres_db: str = "externam"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    # Si fourni, prend le dessus sur les POSTGRES_* (Railway expose DATABASE_URL ; aussi pratique en test).
    database_url_override: str | None = Field(default=None, validation_alias="DATABASE_URL")

    # --- JWT (RS256) ---
    jwt_algorithm: str = "RS256"
    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"
    # Contenu PEM direct (PaaS type Railway, sans fichier) ; prioritaire sur les *_path ci-dessus.
    jwt_private_key: str | None = None
    jwt_public_key: str | None = None
    access_token_expiration: int = 900  # 15 min
    refresh_token_expiration: int = 604800  # 7 jours

    # --- Seed admin (créé au démarrage s'il n'existe pas) ---
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "admin1234"
    seed_admin_firstname: str = "Admin"
    seed_admin_lastname: str = "Externam Hub"

    # --- Tâches planifiées (APScheduler in-process) ---
    # Mettre à false si tu lances un worker séparé ou tournes en multi-process.
    scheduler_enabled: bool = True

    # --- URLs ---
    base_url: str = "http://localhost:8000"
    front_base_url: str = "http://localhost:3000"

    # --- Monitoring ---
    sentry_url: str = ""

    # --- Email (SMTP) ---
    # Tant que SMTP_USER est vide, send_email() log au lieu d'envoyer (dev/test hors-ligne).
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@externam-hub.com"

    # --- Rapports ads hebdo ---
    # Heure (0-23) du cron quotidien ; le jour d'envoi est filtré par client (report_day).
    report_send_hour: int = 9

    # --- Meta Ads (Marketing API) ---
    # Sans META_ACCESS_TOKEN, le provider reste en stub déterministe (dev/test hors-ligne).
    meta_graph_version: str = "v25.0"
    meta_access_token: str = Field(
        default="", validation_alias=AliasChoices("META_ACCESS_TOKEN", "META_ADS_ACCESS_TOKEN")
    )
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_api_timeout: float = 30.0
    meta_max_retries: int = 5
    # Business "partenaire" qui héberge l'utilisateur système (celui du token). S'il est défini,
    # l'app découvre les comptes partagés avec ce business (client_ad_accounts), pas seulement ceux
    # affectés à l'utilisateur système (/me/adaccounts). Un partage de portefeuille suffit alors.
    meta_business_id: str = ""

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
