
import getpass
import shlex
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parents[2]
DATABASE_DIR = ROOT / "database"
MIGRATIONS_DIR = DATABASE_DIR / "migrations"

MIGRATIONS = [
    ("002", "Create schema migrations table"),
    ("001", "Add AI classification fields"),
    ("003", "Create complaint AI reviews"),
    ("004", "Add AI classification started timestamp"),
    ("005", "Add AI classification attempt tracking"),
    ("006", "Create login rate limits"),
]


def extract_connection_url():
    raw = getpass.getpass(
        "Paste latest Neon psql command (hidden): "
    )

    parts = shlex.split(raw)

    url = next(
        (
            part for part in parts
            if part.startswith(("postgresql://", "postgres://"))
        ),
        None,
    )

    if not url:
        raise RuntimeError("Valid PostgreSQL URL not found.")

    return url


def execute_sql(connection, sql):
    statements = [
        line
        for line in sql.splitlines()
        if line.strip().upper() not in {"BEGIN;", "COMMIT;"}
    ]

    with connection.cursor() as cursor:
        cursor.execute("\n".join(statements), prepare=False)


def verify_database_state(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )

        existing_tables = [row[0] for row in cursor.fetchall()]

    if not existing_tables:
        print("Fresh empty Neon database confirmed.")
        return False

    if "schema_migrations" not in existing_tables:
        raise RuntimeError(
            "Database is not empty and has no migration tracking table. "
            "Refusing to modify it."
        )

    print("Existing migration tracking table detected.")
    return True


def apply_migration(connection, version, description):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('public.schema_migrations')"
        )
        tracking_table_exists = cursor.fetchone()[0] is not None

        if tracking_table_exists:
            cursor.execute(
                """
                SELECT 1
                FROM public.schema_migrations
                WHERE version = %s
                """,
                (version,),
            )

            if cursor.fetchone():
                print(f"Migration {version}: already applied.")
                return
        elif version != "002":
            raise RuntimeError(
                "Migration tracking table is missing."
            )

    migration_file = (
        MIGRATIONS_DIR
        / {
            "001": "001_add_ai_classification_fields.sql",
            "002": "002_create_schema_migrations.sql",
            "003": "003_create_complaint_ai_reviews.sql",
            "004": "004_add_ai_classification_started_at.sql",
            "005": "005_add_ai_classification_attempt_tracking.sql",
            "006": "006_create_login_rate_limits.sql",
        }[version]
    )

    sql = migration_file.read_text(encoding="utf-8")
    execute_sql(connection, sql)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.schema_migrations (
                version,
                description
            )
            VALUES (%s, %s)
            ON CONFLICT (version) DO NOTHING
            """,
            (version, description),
        )

    print(f"Migration {version}: SUCCESS")


def main():
    connection_url = extract_connection_url()

    print("Connecting to Neon PostgreSQL...")

    with psycopg.connect(
        connection_url,
        connect_timeout=15,
    ) as connection:

        print("Connected successfully.")

        with connection.transaction():
            database_has_schema = verify_database_state(connection)

            if not database_has_schema:
                schema_file = DATABASE_DIR / "schema.sql"
                execute_sql(
                    connection,
                    schema_file.read_text(encoding="utf-8"),
                )
                print("Base schema: SUCCESS")

            for version, description in MIGRATIONS:
                apply_migration(
                    connection,
                    version,
                    description,
                )

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT version, description
                    FROM public.schema_migrations
                    ORDER BY version
                    """
                )

                applied_migrations = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                    """
                )

                tables = cursor.fetchall()

            expected_versions = {
                version for version, _ in MIGRATIONS
            }

            actual_versions = {
                row[0] for row in applied_migrations
            }

            if not expected_versions.issubset(actual_versions):
                raise RuntimeError(
                    "Migration verification failed."
                )

        print("\nApplied migrations:")
        for row in applied_migrations:
            print(row)

        print("\nDatabase tables:")
        for row in tables:
            print(row[0])

    print("\nNeon database migration completed successfully.")


if __name__ == "__main__":
    main()
