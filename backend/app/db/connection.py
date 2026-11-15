import psycopg

from app.core.config import (
    DB_HOST,
    DB_PORT,
    DB_CONNECT_TIMEOUT_SECONDS,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    validate_database_config,
)


def get_db_connection():
    validate_database_config()

    connection = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=DB_CONNECT_TIMEOUT_SECONDS,
    )

    return connection


def get_db():
    with get_db_connection() as connection:
        yield connection
