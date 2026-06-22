from typing import Annotated

from fastapi import Depends

from app.db.session import DbSession
from app.modules.settings.repository import EmailSettingsRepository


def get_email_settings_repository(db: DbSession) -> EmailSettingsRepository:
    return EmailSettingsRepository(db)


EmailSettingsRepo = Annotated[EmailSettingsRepository, Depends(get_email_settings_repository)]
