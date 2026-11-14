
from psycopg import Connection


def get_ai_classification_metrics(db: Connection) -> dict:
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_complaints,

                COUNT(*) FILTER (
                    WHERE ai_classification_status = 'NOT_STARTED'
                ) AS not_started,

                COUNT(*) FILTER (
                    WHERE ai_classification_status = 'PENDING'
                ) AS pending,

                COUNT(*) FILTER (
                    WHERE ai_classification_status = 'COMPLETED'
                ) AS completed,

                COUNT(*) FILTER (
                    WHERE ai_classification_status = 'FAILED'
                ) AS failed,

                COUNT(*) FILTER (
                    WHERE ai_classification_status = 'SKIPPED'
                ) AS skipped,

                COALESCE(
                    EXTRACT(
                        EPOCH FROM (
                            CURRENT_TIMESTAMP
                            - (
                                MIN(ai_classification_started_at)
                                FILTER (
                                    WHERE ai_classification_status = 'PENDING'
                                )
                            )
                        )
                    ),
                    0
                )::BIGINT AS oldest_pending_age_seconds

            FROM complaints;
            """
        )

        row = cursor.fetchone()

        cursor.execute(
            """
            SELECT
                ai_classification_attempt_count,
                COUNT(*) AS total
            FROM complaints
            GROUP BY ai_classification_attempt_count
            ORDER BY ai_classification_attempt_count;
            """
        )

        attempt_rows = cursor.fetchall()

    return {
        "total_complaints": row[0],
        "not_started": row[1],
        "pending": row[2],
        "completed": row[3],
        "failed": row[4],
        "skipped": row[5],
        "oldest_pending_age_seconds": row[6],
        "attempt_distribution": [
            {
                "attempt_count": attempt_row[0],
                "total": attempt_row[1]
            }
            for attempt_row in attempt_rows
        ]
    }
