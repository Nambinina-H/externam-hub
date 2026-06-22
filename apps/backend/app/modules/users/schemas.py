from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.users.enums import UserRoleEnum


class CreateUserSchema(BaseModel):
    firstname: str = Field(max_length=100)
    lastname: str = Field(max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    company: str = ""
    phone_number: str = ""


class AdminCreateUserSchema(BaseModel):
    """Création d'un membre de l'équipe par un super admin (avec choix du rôle)."""

    model_config = ConfigDict(use_enum_values=True)

    firstname: str = Field(max_length=100)
    lastname: str = Field(max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRoleEnum = UserRoleEnum.META_ADS_EXPERT


class AdminUpdateUserSchema(BaseModel):
    """Mise à jour partielle d'un membre par un super admin. Mot de passe : vide = inchangé."""

    model_config = ConfigDict(use_enum_values=True)

    firstname: str | None = Field(default=None, max_length=100)
    lastname: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    role: UserRoleEnum | None = None
    password: str | None = None


class UserPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    firstname: str
    lastname: str
    email: EmailStr
    company: str | None = None
    phone_number: str | None = None
    role: str
