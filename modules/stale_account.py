"""
stale_accounts.py

Detects and suspends user accounts that have not logged in within the
configured threshold period (default: 90 days).

Real-world equivalent:
    Azure AD Access Reviews / Conditional Access policies that flag or
    block accounts showing no sign-in activity for an extended period.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db.database import get_connection
from config import cfg

STALE_THRESHOLD_DAYS = cfg["accounts"]["stale_threshold_days"]  # default: 90


def detect_stale_accounts(cutoff) -> list[dict]:
    """
    Find all active accounts whose last_login exceeds the stale threshold.

    Real-world equivalent:
        Azure AD Sign-in logs filtered by last_sign_in_date_time,
        or Microsoft Entra Access Reviews targeting inactive users.

    Returns list of user dicts for stale accounts.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id, display_name, email, department, last_login
        FROM users
        WHERE status     =  'active'
          AND last_login IS NOT NULL
          AND last_login <  ?  
    """,
        (cutoff,),
    )

    rows = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows


def suspend_account(user_id: str, cursor) -> None:
    """
    Suspend the account by updating its status to 'suspended' and log the action.
    """
    cursor.execute(
        """
        UPDATE users
        SET status = 'suspended'        
        WHERE user_id = ?
    """,
        (user_id,),
    )


def log_stale_suspension(user_id: str, detail: str, cursor) -> None:
    """
    Write a STALE_SUSPENDED entry to the audit log.

    Real-world equivalent:
        Azure AD audit log entry for sign-in block,
        triggered by Access Review or automated policy.
    """
    cursor.execute(
        """
        INSERT INTO audit_log (action, target_user, detail)
        VALUES ('STALE_SUSPENDED', ?, ?)
    """,
        (user_id, detail),
    )


def detect_never_logged_in() -> list[dict]:
    """
    Find active accounts where last_login is NULL.
    Possible reasons:
      - New hire who hasn't started yet (acceptable)
      - Provisioning error — account created but never activated
      - Test/service account that was forgotten

    This is reported separately from stale accounts — it requires
    **human review** rather than automatic suspension.

    Real-world equivalent:
        Azure AD report: Users with no recorded sign-in activity.
        Microsoft Entra: Users with no sign-in activity
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_id, display_name, email, department, hire_date
        FROM users
        WHERE status     = 'active'
          AND last_login IS NULL
        """
    )
    rows = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows


def run_stale_check() -> dict:
    """
    Full stale account detection and suspension workflow:
        1. Detect stale accounts (depends on last_login)
        2. Suspend each account + write audit log
        3. Report never-logged-in accounts (no auto-action)
        4. Print summary
    """
    cutoff = (datetime.now() - timedelta(days=STALE_THRESHOLD_DAYS)).strftime(
        "%Y-%m-%d"
    )
    print(f"  Cutoff date: {cutoff}")

    # Step 1 — Detect stale accounts
    stale_accounts = detect_stale_accounts(cutoff)
    if not stale_accounts:
        print("\n  No stale accounts detected.\n")
    else:
        print(f"\n  [{len(stale_accounts)}] Stale account(s) detected:\n")

        conn = get_connection()
        cursor = conn.cursor()
        suspended = []
        try:
            for user in stale_accounts:
                print(
                    f"  - {user['display_name']} ({user['email']}) | Last login: {user['last_login']}"
                )
                # Step 2 — Suspend account and log actions
                suspend_account(user["user_id"], cursor)
                detail = (
                    f"Suspended due to inactivity | "
                    f"Last login: {user['last_login']} | "
                    f"Threshold: {STALE_THRESHOLD_DAYS} days"
                )
                log_stale_suspension(user["user_id"], detail, cursor)
                suspended.append(user["user_id"])
            conn.commit()
            print(f"\n  {len(suspended)} account(s) suspended.")
        except Exception as e:
            suspended = []
            conn.rollback()
            print(f"\n[ERROR] Stale check failed, transaction rolled back: {e}")
        finally:
            cursor.close()
            conn.close()

        # Step 3 — Never-logged-in report (report only, no auto-action)
        never_logged_in = detect_never_logged_in()
        if never_logged_in:
            print(
                f"\n  [{len(never_logged_in)}] Never-logged-in account(s) detected — manual review required\n"
            )
            for user in never_logged_in:
                print(
                    f"  [?] {user['display_name']} ({user['user_id']}) | "
                    f"Dept: {user['department']} | "
                    f"Hired: {user['hire_date']}"
                )

        return {
            "suspended": suspended,
            "never_logged_in": [u["user_id"] for u in never_logged_in],
        }


if __name__ == "__main__":
    run_stale_check()
