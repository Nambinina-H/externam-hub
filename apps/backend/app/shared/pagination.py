from dataclasses import dataclass
from typing import Annotated, Generic, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


@dataclass
class PaginationParams:
    """Paramètres de pagination (offset/limit)."""

    page: int = 1
    size: int = 20

    @property
    def limit(self) -> int:
        return self.size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


def get_pagination(
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationParams:
    return PaginationParams(page=page, size=size)


# Dépendance typée réutilisable dans les routers (fonction -> instance, cf. skill FastAPI)
PaginationDep = Annotated[PaginationParams, Depends(get_pagination)]


class Page(BaseModel, Generic[T]):
    """Enveloppe de réponse paginée (aligné sur PaginatedResult<T> côté frontend)."""

    items: list[T]
    total: int
    page: int
    size: int


def paginate(db: Session, stmt, params: PaginationParams) -> tuple[list, int]:
    """Applique limit/offset à un `select` et renvoie (items, total)."""
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.execute(stmt.limit(params.limit).offset(params.offset)).scalars().all()
    return items, total
