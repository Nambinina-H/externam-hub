from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.clients.enums import DayOfWeekEnum


class ClientCreateSchema(BaseModel):
    # use_enum_values : les champs enum sont stockés/validés comme leur valeur (str/int).
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(max_length=150)
    company: str | None = Field(default=None, max_length=150)
    contact_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=50)
    emails: list[EmailStr] = Field(default_factory=list)
    meta_business_id: str | None = Field(default=None, max_length=100)
    meta_ad_account_id: str | None = Field(default=None, max_length=100)
    report_day: DayOfWeekEnum = DayOfWeekEnum.MONDAY
    is_active: bool = True


class ClientUpdateSchema(BaseModel):
    """Mise à jour partielle : tous les champs sont optionnels."""

    model_config = ConfigDict(use_enum_values=True)

    name: str | None = Field(default=None, max_length=150)
    company: str | None = Field(default=None, max_length=150)
    contact_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=50)
    emails: list[EmailStr] | None = None
    meta_business_id: str | None = Field(default=None, max_length=100)
    meta_ad_account_id: str | None = Field(default=None, max_length=100)
    managed_campaign_ids: list[str] | None = None
    report_day: DayOfWeekEnum | None = None
    is_active: bool | None = None


class ClientPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str | None = None
    contact_name: str | None = None
    phone: str | None = None
    emails: list[str] = Field(default_factory=list)
    meta_business_id: str | None = None
    meta_ad_account_id: str | None = None
    managed_campaign_ids: list[str] = Field(default_factory=list)
    report_day: int
    is_active: bool
    last_report_sent_at: datetime | None = None
    created_at: datetime

    @field_validator("emails", "managed_campaign_ids", mode="before")
    @classmethod
    def _list_default(cls, value):
        # Tolère les lignes héritées où la colonne (emails / campagnes) est NULL.
        return value or []


# --- Import CSV ---


class ImportPreviewRequest(BaseModel):
    csv: str


class ImportMapping(BaseModel):
    """Quelle colonne CSV alimente quel champ interne (le nom de la colonne, ou None)."""

    name: str | None = None
    company: str | None = None
    emails: str | None = None
    contact_name: str | None = None
    phone: str | None = None


class SendReportRequest(BaseModel):
    """Emails destinataires choisis pour l'envoi (sinon : tous les emails du client)."""

    to: list[EmailStr] | None = None


class ImportRequest(BaseModel):
    csv: str
    mapping: ImportMapping
    # Si vrai : après l'import, tente de lier chaque client non lié à un portefeuille business
    # par cohérence (nom / entreprise / domaine email vs nom du portefeuille et des comptes).
    auto_link: bool = False
