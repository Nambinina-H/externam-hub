from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.reports.models import EmailTemplate


class EmailTemplateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_base(self) -> EmailTemplate | None:
        stmt = select(EmailTemplate).where(EmailTemplate.client_id.is_(None))
        return self.db.execute(stmt).scalars().first()

    def get_for_client(self, client_id: int) -> EmailTemplate | None:
        stmt = select(EmailTemplate).where(EmailTemplate.client_id == client_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def override_client_ids(self) -> list[int]:
        stmt = select(EmailTemplate.client_id).where(EmailTemplate.client_id.is_not(None))
        return list(self.db.execute(stmt).scalars().all())

    def add(self, template: EmailTemplate) -> EmailTemplate:
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def save(self, template: EmailTemplate) -> EmailTemplate:
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete(self, template: EmailTemplate) -> None:
        self.db.delete(template)
        self.db.commit()
