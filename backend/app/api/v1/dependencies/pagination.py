from dataclasses import dataclass

from fastapi import Query


@dataclass
class PaginationParams:
    page: int
    size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


def pagination_params(
    page: int = Query(1, ge=1, description="1-indexed page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginationParams:
    return PaginationParams(page=page, size=size)
