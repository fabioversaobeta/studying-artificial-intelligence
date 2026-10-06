"""Reusable limit/offset pagination for list endpoints.

The response body stays a plain JSON array (the frontend depends on that);
the total number of matching rows is returned in the `X-Total-Count` header.
"""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query, Response

DEFAULT_LIMIT = 50
MAX_LIMIT = 200
TOTAL_COUNT_HEADER = "X-Total-Count"


@dataclass(frozen=True)
class PageParams:
    limit: int
    offset: int


def get_page_params(
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT, description="Max items to return")] = (
        DEFAULT_LIMIT
    ),
    offset: Annotated[int, Query(ge=0, description="Items to skip")] = 0,
) -> PageParams:
    return PageParams(limit=limit, offset=offset)


Pagination = Annotated[PageParams, Depends(get_page_params)]


def set_total_count(response: Response, total: int) -> None:
    response.headers[TOTAL_COUNT_HEADER] = str(total)
