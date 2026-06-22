from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.auth.security import hash_password
from app.modules.users.enums import UserRoleEnum
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


def seed_admin(db: Session) -> User | None:
    """Crée l'utilisateur admin défini par les settings `SEED_ADMIN_*`.

    Idempotent : ne fait rien si un utilisateur avec cet email existe déjà.
    """
    settings = get_settings()
    repo = UserRepository(db)
    if repo.get_by_email(settings.seed_admin_email):
        return None

    admin = User(
        firstname=settings.seed_admin_firstname,
        lastname=settings.seed_admin_lastname,
        email=settings.seed_admin_email,
        password=hash_password(settings.seed_admin_password),
        role=UserRoleEnum.SUPERADMIN.value,
    )
    return repo.create(admin)
