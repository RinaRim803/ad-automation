"""
offboarding.py

Handles departing employee account deactivation and access removal.

Real-world equivalent:
    IT team receiving a termination notice from HR and performing:
      - Account deactivation in Active Directory / Azure AD
      - Removal from all security groups
      - Transfer to Offboarded group for audit tracking
      - Audit log entry for compliance requirements
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


from db.database import get_connection
from config import cfg


def validate_offboard_target(user_id: str) -> list[str]:
    """
    Validate that the target account exists and is eligible for offboarding.

    Validation targets and reasons
    [EXISTENCE CHECK]
    - user_id       : Attempting to offboard a non-existent account may result in
                      no action being performed and leave incorrect records in the audit log.

    [STATUS CHECK]
    - status        : Attempting to offboard an account that is already 'inactive' may
                      result in duplicate processing and contaminate the audit log. Only accounts currently in 'active' status should be processed.

    """

    errors = []

    # Check if user exists and is active
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, status FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        errors.append(f"User not found: '{user_id}'")
    elif row["status"] == "inactive":
        errors.append(f"User '{user_id}' is already inactive. Offboarding skipped.")

    cursor.close()
    conn.close()

    return errors


def deactivate_account(user_id: str, termination_date: str, cursor) -> None:
    """
    Set user status to 'inactive' and record termination date.

    Real-world equivalent:
        Disable-ADAccount in PowerShell / disabling a user in Azure AD portal.
        Account is NOT deleted — retained for audit, legal hold, and data recovery.

    Why deactivate instead of delete:
        Deleting a user immediately removes their mailbox, OneDrive, and group
        history. Deactivation preserves the record for compliance and allows
        the account to be reactivated if termination was entered in error.

    """

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        UPDATE users
        SET status           = 'inactive',
            termination_date = ?,
            updated_at       = ?
        WHERE user_id = ?""",
        (termination_date, now, user_id),
    )


def remove_all_groups(user_id: str, cursor) -> list[str]:
    """
    Remove user from all security groups, then add to Offboarded group.
    Real-world equivalent:
        Removing a user from all Azure AD security groups and M365 licenses
        to revoke access to all connected resources (SharePoint, Teams, VPN, etc.)

    Why remove groups before adding Offboarded:
        Access revocation must be complete before the account is marked as
        offboarded. Leaving any group membership active would retain resource
        access even after the account is disabled.

    Returns list of groups that were removed.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Fetch current group memberships before removal
    cursor.execute(
        """
        SELECT group_name FROM user_groups WHERE user_id = ?
    """,
        (user_id,),
    )
    current_groups = [row["group_name"] for row in cursor.fetchall()]

    # Remove all group memberships
    cursor.execute("DELETE FROM user_groups WHERE user_id = ?", (user_id,))

    # Add to Offboarded group for audit tracking
    cursor.execute(
        """
        INSERT OR IGNORE INTO user_groups (user_id, group_name, added_at)
        VALUES (?, 'Offboarded', ?)
    """,
        (user_id, now),
    )

    return current_groups


def log_offboard(user_id: str, detail: str, cursor) -> None:
    """
    Write an audit log entry for the offboarding action.

    Real-world equivalent:
        Azure AD audit log entry for account deactivation.
        Required for SOC 2, ISO 27001, and legal hold compliance.
        This is critical for legal and regulatory requirements to demonstrate proper handling of departing employee accounts.
    """
    cursor.execute(
        """
        INSERT INTO audit_log (action, target_user, detail)
        VALUES ('OFFBOARD', ?, ?)
        """,
        (user_id,detail,),
    )


def offboard_user(user_id: str, termination_date: str) -> bool:
    """
    Offboard a user by deactivating their account and removing access.

    Full offboarding workflow:
        1. Validate target account exists and is active
        2. Update user status to 'inactive' and set termination_date
        3. Remove from all groups and add to 'Offboarded' group
        4. Write audit log entry for compliance tracking
        5. Print summary of actions taken
    Returns True on success, False on failure.
    """
    print(f"  OFFBOARDING: {user_id}")

    # Step 1 — Validate
    errors = validate_offboard_target(user_id)
    if errors:
        print("[ERROR] Validation failed:")
        for e in errors:
            print(f"  - {e}")
        return False

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT display_name FROM users WHERE user_id = ?", (user_id,))
        display_name = cursor.fetchone()["display_name"]
        # Step 2 — Deactivate account and set termination date
        deactivate_account(user_id, termination_date, cursor)
        print(f"  [-] Account deactivated: {display_name}")

        # Step 3 — Remove from all groups and add to 'Offboarded' group
        removed_groups = remove_all_groups(user_id, cursor)
        if removed_groups:
            print(f"  [-] Groups removed: {', '.join(removed_groups)}")
        else:
            print(f"  [-] No active group memberships found.")
        print(f"  [+] Added to: Offboarded")

        # Step 4 — Write audit log entry
        detail = (
            f"Offboarded {display_name} | "
            f"Termination date: {termination_date or 'today'} | "
            f"Groups removed: {', '.join(removed_groups) if removed_groups else 'none'}"
        )
        log_offboard(user_id, detail, cursor)
        print(f"  [+] Audit log recorded.")

        conn.commit()
        print(f"\n  Offboarding complete for {display_name}.")
        return True

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Offboarding failed, transaction rolled back: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # U1007 Lisa Wang — already seeded as inactive (tests duplicate guard)
    # U1011 Jane Smith — active account (tests normal offboarding flow)
    offboard_user("U1011", termination_date="2026-04-04")
