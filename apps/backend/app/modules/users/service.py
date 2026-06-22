from app.core.errors import BadRequestError, NotFoundError
from app.modules.auth.security import hash_password
from app.modules.users.models import User
from app.shared.pagination import Page, PaginationParams
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import AdminCreateUserSchema, AdminUpdateUserSchema, UserPublicSchema


def list_users(repo: UserRepository, params: PaginationParams) -> Page[UserPublicSchema]:
    items, total = repo.list_paginated(params)
    return Page[UserPublicSchema](
        items=[UserPublicSchema.model_validate(user) for user in items],
        total=total,
        page=params.page,
        size=params.size,
    )


def create_user(repo: UserRepository, data: AdminCreateUserSchema) -> UserPublicSchema:
    if repo.get_by_email(data.email):
        raise BadRequestError("Un utilisateur avec cet email existe déjà.")
    user = User(
        firstname=data.firstname,
        lastname=data.lastname,
        email=data.email,
        password=hash_password(data.password),
        role=data.role,
        company="",
        phone_number="",
    )
    created = repo.create(user)
    return UserPublicSchema.model_validate(created)


def _get_user(repo: UserRepository, user_id: int) -> User:
    user = repo.get_by_id(user_id)
    if not user:
        raise NotFoundError("Utilisateur introuvable")
    return user


def update_user(repo: UserRepository, user_id: int, data: AdminUpdateUserSchema) -> UserPublicSchema:
    user = _get_user(repo, user_id)
    fields = data.model_dump(exclude_unset=True)

    new_email = fields.get("email")
    if new_email:
        existing = repo.get_by_email(new_email)
        if existing and existing.id != user.id:
            raise BadRequestError("Un utilisateur avec cet email existe déjà.")

    password = fields.pop("password", None)
    if password:  # vide / absent -> mot de passe inchangé
        user.password = hash_password(password)

    for key, value in fields.items():
        if value is not None:
            setattr(user, key, value)

    saved = repo.save(user)
    return UserPublicSchema.model_validate(saved)


def delete_user(repo: UserRepository, user_id: int) -> None:
    repo.delete(_get_user(repo, user_id))
