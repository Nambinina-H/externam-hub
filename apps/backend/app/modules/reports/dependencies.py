from typing import Annotated

from fastapi import Depends

from app.db.session import DbSession
from app.modules.reports.repository import EmailTemplateRepository


def get_email_template_repository(db: DbSession) -> EmailTemplateRepository:
    return EmailTemplateRepository(db)


EmailTemplateRepo = Annotated[EmailTemplateRepository, Depends(get_email_template_repository)]
