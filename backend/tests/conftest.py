import os

import psycopg
import pytest


@pytest.fixture
def postgres_connection():
    password = os.getenv("CAMPUSCARE_TEST_DB_PASSWORD")

    if not password:
        pytest.skip(
            "CAMPUSCARE_TEST_DB_PASSWORD is not configured."
        )

    connection = psycopg.connect(
        host="localhost",
        port=5432,
        dbname="campuscare_ai_test",
        user="campuscare_test_user",
        password=password,
        connect_timeout=5,
    )

    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()
