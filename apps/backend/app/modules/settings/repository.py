from sqlalchemy.orm import Session

from app.modules.settings.models import EmailSettings

_SINGLETON_ID = 1


class EmailSettingsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self) -> EmailSettings | None:
        return self.db.get(EmailSettings, _SINGLETON_ID)

    def upsert(self, **fields) -> EmailSettings:
        row = self.get()
        if row is None:
            row = EmailSettings(id=_SINGLETON_ID, **fields)
            self.db.add(row)
        else:
            for key, value in fields.items():
                setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return row
