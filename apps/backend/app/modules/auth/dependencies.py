from typing import Annotated

from fastapi import Depends

from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import oauth2_scheme
from app.shared.utils import to_dict
from app.modules.auth.security import decode_token
from app.modules.users.dependencies import UserRepo
from app.modules.users.enums import UserRoleEnum


def get_authenticated_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    repo: UserRepo,
) -> dict:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid token type")

        user_id = payload.get("id")
        if not user_id:
            raise UnauthorizedError("The token is invalid or has expired.")

        user = repo.get_by_id(user_id)
        if not user or user.is_blacklisted:
            raise UnauthorizedError("User not found or blacklisted")

        data = to_dict(user)
        data.pop("password", None)
        return data
    except UnauthorizedError:
        raise
    except Exception as exp:
        raise UnauthorizedError("The token is invalid or has expired.") from exp


def require_roles(*roles: str):
    """Fabrique une dépendance qui exige l'un des rôles donnés (lit le rôle en base)."""

    allowed = set(roles)

    def _checker(current_user: dict = Depends(get_authenticated_user)) -> dict:
        if current_user.get("role") not in allowed:
            raise ForbiddenError("Accès refusé pour votre rôle.")
        return current_user

    return _checker


# ADMIN est conservé comme équivalent legacy de SUPERADMIN (accès total).
require_superadmin = require_roles(UserRoleEnum.SUPERADMIN.value, UserRoleEnum.ADMIN.value)
require_meta_ads = require_roles(
    UserRoleEnum.SUPERADMIN.value, UserRoleEnum.ADMIN.value, UserRoleEnum.META_ADS_EXPERT.value
)
# Rétro-compat : ancien nom encore importé par certains modules.
require_admin_or_superadmin = require_superadmin


# Dépendances typées réutilisables
CurrentUser = Annotated[dict, Depends(get_authenticated_user)]
AdminUser = Annotated[dict, Depends(require_superadmin)]
