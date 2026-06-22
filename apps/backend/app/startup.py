from sqlalchemy import inspect, text

from app import models  # noqa: F401  (enregistre les modèles)
from app.core.config import get_settings
from app.db.base import Base, engine
from app.db.session import SessionLocal
from app.modules.users.seed import seed_admin


def _reconcile_local_columns() -> None:
    """En local, `create_all` crée les tables manquantes mais ne MODIFIE pas
    les tables existantes. On ajoute donc les colonnes absentes des modèles
    (jamais de suppression) pour éviter de recréer la base à chaque nouvelle colonne.
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in tables:
            continue  # table neuve : déjà complète via create_all
        existing = {col["name"] for col in inspector.get_columns(table.name)}
        indexes = inspector.get_indexes(table.name)
        model_columns = {column.name for column in table.columns}

        # 1) Colonnes du modèle absentes en base -> on les ajoute.
        for column in table.columns:
            if column.name in existing:
                continue
            col_type = column.type.compile(dialect=engine.dialect)
            ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'
            try:
                with engine.begin() as conn:
                    conn.execute(text(ddl))
                print(f"[startup] Colonne ajoutee: {table.name}.{column.name}")
            except Exception as exc:  # ne pas bloquer le démarrage pour un ALTER
                print(f"[startup] Ajout colonne {table.name}.{column.name} ignore: {exc}")

        # 2) Colonnes héritées absentes du modèle -> on les supprime (sinon une vieille
        #    colonne NOT NULL casse les INSERT). On retire d'abord les index qui les référencent
        #    (contrainte SQLite : DROP COLUMN interdit sur une colonne indexée).
        for db_col in existing - model_columns:
            try:
                with engine.begin() as conn:
                    for idx in indexes:
                        if idx.get("name") and db_col in (idx.get("column_names") or []):
                            conn.execute(text(f'DROP INDEX IF EXISTS "{idx["name"]}"'))
                    conn.execute(text(f'ALTER TABLE "{table.name}" DROP COLUMN "{db_col}"'))
                print(f"[startup] Colonne supprimee: {table.name}.{db_col}")
            except Exception as exc:
                print(f"[startup] Suppression colonne {table.name}.{db_col} ignore: {exc}")


def startup_setup() -> None:
    """Initialisation au démarrage de l'application.

    - test    : DB et seed gérés par les fixtures pytest → on ne touche à rien.
    - local   : on crée les tables manquantes (démarrage rapide sans migration).
    - prod    : la source de vérité reste Alembic (`alembic upgrade head`) ; ici on seed l'admin.
    """
    settings = get_settings()

    if settings.environment == "test":
        return

    if settings.environment == "local":
        Base.metadata.create_all(bind=engine)
        _reconcile_local_columns()
        print("[startup] Tables synchronisées (mode local).")

    # Seed de l'admin (idempotent : uniquement s'il n'existe pas).
    db = SessionLocal()
    try:
        created = seed_admin(db)
        if created:
            print(f"[startup] Admin seedé : {settings.seed_admin_email}")
    except Exception as exp:  # ne pas faire planter le démarrage pour un souci de seed
        print(f"[startup] Seed admin ignoré : {exp}")
    finally:
        db.close()

    print(f"[startup] Externam Hub API démarrée - environnement: {settings.environment}")
