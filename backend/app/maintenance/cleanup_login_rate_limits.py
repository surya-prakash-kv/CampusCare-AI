
from app.db.connection import get_db_connection
from app.services.login_rate_limit import (
    cleanup_expired_login_rate_limits,
)


def main() -> None:
    with get_db_connection() as db:
        deleted_count = cleanup_expired_login_rate_limits(db)

    print(
        f"Login rate-limit cleanup completed. "
        f"Deleted records: {deleted_count}"
    )


if __name__ == "__main__":
    main()
