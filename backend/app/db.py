from collections.abc import Iterator
from contextlib import contextmanager

from psycopg import Connection
from psycopg_pool import ConnectionPool

from app.config import get_settings

pool = ConnectionPool(
    conninfo=get_settings().database_url,
    min_size=0,
    max_size=5,
    open=False,
)


def open_pool() -> None:
    if pool.closed:
        pool.open()


def close_pool() -> None:
    if not pool.closed:
        pool.close()


@contextmanager
def get_connection() -> Iterator[Connection]:
    open_pool()
    with pool.connection() as connection:
        yield connection
