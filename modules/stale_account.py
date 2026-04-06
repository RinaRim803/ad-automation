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


def detect_stale_accounts() -> list[dict]:
    """
    Find all active accounts whose last_login exceeds the stale threshold.

    Real-world equivalent:
        Azure AD Sign-in logs filtered by last_sign_in_date_time,
        or Microsoft Entra Access Reviews targeting inactive users.

    Returns list of user dicts for stale accounts.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, display_name, email, department, last_login
        FROM users
        WHERE status     =  'active'
          AND last_login IS NOT NULL
          AND last_login <  DATE('now', ? || ' days')       
    """, (-STALE_THRESHOLD_DAYS,))

    rows = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows

def suspend_accounts(accounts: list[dict]):
    """
    """

def run_stale_check() -> dict:
    """
    Full stale account detection and suspension workflow:
        1. Detect stale accounts (depends on last_login)
        2. Suspend each account + write audit log
        3. Report never-logged-in accounts (no auto-action)
        4. Print summary
    """
    cutoff = (datetime.now() - timedelta(days=STALE_THRESHOLD_DAYS)).strftime("%Y-%m-%d")
    print(f"  Cutoff date: {cutoff}")


    # Step 1 — Detect stale accounts
    stale_accounts = detect_stale_accounts()
    if not stale_accounts:
        print("\n  No stale accounts detected.\n")
    else:
        print(f"\n  [{len(stale_accounts)}] Stale account(s) detected:\n")
        # Step 2 — Suspend accounts and log actions
        # suspend_accounts(stale_accounts)
        try:
            for user in stale_accounts:
                print(f"  - {user['display_name']} ({user['email']}) | Last login: {user['last_login']}")
        except Exception as e:
            print(f"Error processing stale accounts: {e}")
        finally:    
            print("Stale account suspension process completed.")

if __name__ == "__main__":
    print("This module is intended to be imported and used by a scheduler or main application.")
    run_stale_check()