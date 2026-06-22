from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.modules.auth import service
from app.modules.auth.schemas import RefreshRequestSchema, TokenSchema, UserLoginSchema
from app.modules.users.dependencies import UserRepo
from app.modules.users.schemas import CreateUserSchema

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenSchema, status_code=201)
def register(payload: CreateUserSchema, repo: UserRepo):
    return service.register_user(repo, payload)


@router.post("/login", response_model=TokenSchema)
def login(payload: UserLoginSchema, repo: UserRepo):
    return service.login_user(repo, payload)


@router.post("/token", response_model=TokenSchema, include_in_schema=False)
def token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], repo: UserRepo):
    return service.login_user(repo, UserLoginSchema(email=form_data.username, password=form_data.password))


@router.post("/refresh", response_model=TokenSchema)
def refresh(payload: RefreshRequestSchema, repo: UserRepo):
    return service.refresh_tokens(repo, payload.refresh_token)
