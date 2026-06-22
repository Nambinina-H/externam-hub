from fastapi import APIRouter, Depends, status

from app.core.errors import BadRequestError
from app.shared.pagination import Page, PaginationDep
from app.modules.auth.dependencies import CurrentUser, require_superadmin
from app.modules.users import service
from app.modules.users.dependencies import UserRepo
from app.modules.users.schemas import AdminCreateUserSchema, AdminUpdateUserSchema, UserPublicSchema

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserPublicSchema)
def me(current_user: CurrentUser):
    return current_user


@router.get("", response_model=Page[UserPublicSchema], dependencies=[Depends(require_superadmin)])
def list_users(repo: UserRepo, params: PaginationDep):
    return service.list_users(repo, params)


@router.post(
    "",
    response_model=UserPublicSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_superadmin)],
)
def create_user(payload: AdminCreateUserSchema, repo: UserRepo):
    return service.create_user(repo, payload)


@router.patch("/{user_id}", response_model=UserPublicSchema, dependencies=[Depends(require_superadmin)])
def update_user(user_id: int, payload: AdminUpdateUserSchema, repo: UserRepo, current_user: CurrentUser):
    # Garde-fou : on ne peut pas changer son propre rôle (risque de se verrouiller dehors).
    if user_id == current_user["id"] and payload.role is not None and payload.role != current_user["role"]:
        raise BadRequestError("Vous ne pouvez pas modifier votre propre rôle.")
    return service.update_user(repo, user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_superadmin)])
def delete_user(user_id: int, repo: UserRepo, current_user: CurrentUser):
    if user_id == current_user["id"]:
        raise BadRequestError("Vous ne pouvez pas supprimer votre propre compte.")
    service.delete_user(repo, user_id)
