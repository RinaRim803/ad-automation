
import csv
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db.database import get_connection, init_db
from config import cfg, ROOT_DIR

USERS_CSV      = ROOT_DIR / cfg["data"]["users_csv"]
DEFAULT_GROUPS = cfg["groups"]["default_groups"]


def seed_groups(cursor):
    """Insert default security groups from config.json."""
    for group in DEFAULT_GROUPS:
        cursor.execute("""
            INSERT OR IGNORE INTO groups (group_name, department, description)
            VALUES (?, ?, ?)
        """, (group["group_name"], group["department"], group["description"]))
    print(f"[Seed] {len(DEFAULT_GROUPS)} groups loaded.")


def seed_users(cursor):
    """Import users from CSV into the users table."""
    with open(USERS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            cursor.execute("""
                INSERT OR IGNORE INTO users (
                    user_id, display_name, email, department, job_title,
                    status, last_login, hire_date, termination_date,
                    manager_email, license
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["user_id"],
                row["display_name"],
                row["email"],
                row["department"],
                row["job_title"],
                row["status"],
                row["last_login"] or None,
                row["hire_date"],
                row["termination_date"] or None,
                row["manager_email"] or None,
                row["license"],
            ))
            count += 1
    print(f"[Seed] {count} users loaded.")


def run():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    seed_groups(cursor)
    seed_users(cursor)
    conn.commit()
    cursor.close()
    conn.close()
    print("[Seed] Database ready.")


if __name__ == "__main__":
    run()