from pydantic import BaseModel, Field


class EmailTemplateSchema(BaseModel):
    subject: str = Field(min_length=1, max_length=300)
    intro: str = Field(max_length=5000)
    closing: str = Field(max_length=5000)
    # Bloc signature libre — le séparateur « -- » est ajouté automatiquement au rendu.
    signature: str = Field(default="", max_length=5000)


class EmailTemplateView(EmailTemplateSchema):
    # Pour une vue par client : True = surcharge propre, False = hérité du modèle de base.
    is_override: bool = False


class TemplatePreviewRequest(EmailTemplateSchema):
    # Aperçu en direct d'un modèle non encore enregistré (avec données d'exemple).
    client_id: int | None = None
