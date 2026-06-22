from app.core.errors import ConflictError, ForbiddenError, UnauthorizedError
from app.modules.auth.schemas import UserLoginSchema
from app.modules.auth.security import build_token_pair, decode_token, hash_password, verify_password
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import CreateUserSchema


def register_user(repo: UserRepository, payload: CreateUserSchema) -> dict:
    if repo.get_by_email(payload.email):
        raise ConflictError(f"User with email '{payload.email}' already exists")

    user = User(
        firstname=payload.firstname,
        lastname=payload.lastname,
        email=payload.email,
        password=hash_password(payload.password),
        company=payload.company,
        phone_number=payload.phone_number,
    )
    user = repo.create(user)
    return build_token_pair(user)


def login_user(repo: UserRepository, payload: UserLoginSchema) -> dict:
    user = repo.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.password):
        raise UnauthorizedError("Invalid email or password")
    if user.is_blacklisted:
        raise ForbiddenError("This account has been blocked")
    return build_token_pair(user)


def refresh_tokens(repo: UserRepository, refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
    except Exception as exp:
        raise UnauthorizedError("Invalid or expired refresh token") from exp

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid token type")

    user = repo.get_by_id(payload.get("id"))
    if not user or user.is_blacklisted:
        raise UnauthorizedError("User not found or blacklisted")
    return build_token_pair(user)
