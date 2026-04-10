"""
One-time cleanup script: remove duplicate SubscriptionUsage rows.

The old renewal flow always INSERT-ed a new SubscriptionUsage row instead of
resetting the existing one.  That leaves multiple rows per subscription_id.
The transcription route uses .scalar() which returns the first row ordered by
primary key — often the stale row with high minutes_used — so the quota never
reset on renewal.

This script keeps only the row with the HIGHEST id per subscription_id
(the most recently inserted one, which should have minutes_used == 0 from the
last renewal) and deletes all older duplicates.

Run once after deploying the fix in users.py:
    cd /Users/shigpi/Files/Islington/year\ 3/FYP
    python -m backend.cleanup_duplicate_usage
"""
from sqlalchemy import text
from backend.core.database import SessionLocal

def main():
    db = SessionLocal()
    try:
        # Find subscription_ids that have more than one usage row
        result = db.execute(
            text("""
                SELECT subscription_id, COUNT(*) as cnt
                FROM subscription_usage
                GROUP BY subscription_id
                HAVING COUNT(*) > 1
            """)
        ).fetchall()

        if not result:
            print("No duplicate SubscriptionUsage rows found. Nothing to clean up.")
            return

        print(f"Found {len(result)} subscription(s) with duplicate usage rows:")
        for row in result:
            print(f"  subscription_id={row.subscription_id}  rows={row.cnt}")

        # Delete all rows except the one with the highest id per subscription_id
        db.execute(
            text("""
                DELETE FROM subscription_usage
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM subscription_usage
                    GROUP BY subscription_id
                )
            """)
        )
        db.commit()
        print("Cleanup complete — duplicate rows removed, newest row retained per subscription.")
    except Exception as exc:
        db.rollback()
        print(f"Cleanup failed: {exc}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
