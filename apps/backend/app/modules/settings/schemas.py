from pydantic import BaseModel, EmailStr, Field


class EmailSettingsPublic(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    from_email: str
    from_name: str = ""
    # On n'expose JAMAIS le mot de passe : seulement s'il est défini.
    password_set: bool
    source: str  # "db" (configuré via l'interface) ou "env" (.env)


class EmailSettingsUpdate(BaseModel):
    smtp_host: str = Field(min_length=1, max_length=255)
    smtp_port: int = Field(ge=1, le=65535)
    smtp_user: str = Field(min_length=1, max_length=255)
    from_email: EmailStr
    from_name: str = Field(default="", max_length=150)
    # Laisser vide pour conserver le mot de passe déjà enregistré.
    smtp_password: str | None = None


class TestEmailRequest(BaseModel):
    to: EmailStr
