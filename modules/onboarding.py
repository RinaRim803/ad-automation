"""
onboarding.py

Handles new employee account creation and initial group assignment.

Real-world equivalent:
    IT team receiving a new hire request from HR and performing:
      - Account provisioning in Active Directory / Azure AD
      - License assignment (M365)
      - Security group membership based on department
      - Audit log entry for compliance tracking
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


from db.database import get_connection
from config import cfg

DEPT_GROUP_MAP = cfg["groups"]["department_group_map"]
DEFAULT_LICENSE = cfg["accounts"]["default_license"]
VALID_STATUSES = cfg["accounts"]["valid_statuses"]
VALID_LICENSES = cfg["accounts"]["valid_licenses"]

REQUIRED_FIELDS = ["user_id", "display_name", "email", "department", "hire_date"]


def validate_new_user(data: dict) -> list[str]:
    """
    Validate input before account creation.

    Prevents ghost accounts, UPN conflicts, and injection risks
    before any DB or AD operation is attempted.


    """
    errors = []

    # Check required fields
    for field in REQUIRED_FIELDS:
        if not data.get(field, "").strip():
            errors.append(f"Missing required field: '{field}'")

    # Validate email format (simple regex)
    email = data.get("email", "")
    if "@" not in email or "." not in email.split("@")[-1]:
        errors.append(f"Invalid email format: '{email}'")

    # Check license value
    license_val = data.get("license", DEFAULT_LICENSE)
    if license_val not in VALID_LICENSES:
        errors.append(f"Invalid license '{license_val}'. Valid: {VALID_LICENSES}")

    # Check for duplicate email in DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        errors.append(f"Email already exists: '{email}'")

    # Check for duplicate user_id in DB
    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ?", (data.get("user_id"),)
    )
    if cursor.fetchone():
        errors.append(f"user_id already exists: '{data.get('user_id')}'")

    cursor.close()
    conn.close()

    return errors


def create_account(user_info: dict, cursor) -> None:
    """
    Insert new user record into 'users' table.

    Args:
        user_info (dict): User information to insert.
        cursor: Database cursor for executing SQL commands.

    Real-world equivalent:
    New-ADUser in PowerShell / creating a user object in Azure AD portal.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """ 
        INSERT INTO users (
            user_id, display_name, email, department, job_title,
            status,hire_date, manager_email, license,
            created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?,'active', ?, ?, ?, ?, ?)
        """,
        (
            user_info["user_id"],
            user_info["display_name"],
            user_info["email"],
            user_info["department"],
            user_info.get("job_title", ""),
            user_info["hire_date"],
            user_info.get("manager_email", ""),
            user_info.get("license", DEFAULT_LICENSE),
            now,
            now,
        ),
    )


#


def assign_default_groups(user_id: str, department: str, cursor) -> list[str]:
    """
    Assign user to default security groups based on department.
    Temporarily, I will assign licenses as groups for simplicity for now in MVP.

    Args:
        user_id (str): User ID to assign groups to.
        department (str): User's department for group mapping.
        cursor: Database cursor for executing SQL commands.

    Real-world equivalent:
    Adding a user to security groups in Active Directory / Azure AD based on their department.
    """

    groups_assigned = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Department group (e.g. Sales → Sales-Team)
    dept_group = DEPT_GROUP_MAP.get(department)
    groups_to_add = ["M365-Licensed"]  # Default license group

    if dept_group:
        groups_to_add.append(dept_group)

    for group_name in groups_to_add:
        cursor.execute(
            """ 
                INSERT INTO user_groups (user_id, group_name, added_at)
                VALUES (?, ?, ?)
                """,
            (user_id, group_name, now),
        )
        groups_assigned.append(group_name)

    return groups_assigned


def log_onboard(user_id: str, detail: str, cursor) -> None:
    """
    Write an ONBOARD entry to the audit log.

    Real-world equivalent:
        Azure AD audit log / M365 compliance center provisioning record.
        Required for SOC 2, ISO 27001 compliance.
    """
    cursor.execute(
        """
        INSERT INTO audit_log (action, target_user, detail)
        VALUES ('ONBOARD', ?, ?)
        """,
        (user_id, detail),
    )


def onboard_user(user_info: dict) -> bool:
    """
    Onboard a new user based on provided information.
    Full onboarding workflow:
        1. Validate input
        2. Create account
        3. Assign default groups
        4. Write audit log
        5. Print summary 
    Returns True on success, False on failure.


    Args:
        user_info (dict): { "user_id": "U1002", ... (same fields as users table)}
    """

    print(f"  ONBOARDING: {user_info.get('display_name')} ({user_info.get('user_id')})")

    # Step 1 — Validate input data
    errors = validate_new_user(user_info)
    if errors:
        print(f"  [ERROR] Validation failed: {errors}")
        for e in errors:
            print(f"  - {e}")
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Step 2 — Create user account in 'users' table
        create_account(user_info, cursor)
        print(f"  [+] Account created: {user_info['email']}")

        # Step 3 — Assign to security and license group
        groups = assign_default_groups(
            user_info["user_id"], user_info["department"], cursor
        )
        print(f"  [+] Assigned to groups: {groups}")

        # Step 4 — Log actions in 'audit_log' table
        detail = (
            f"Onboarded {user_info['display_name']} | "
            f"Dept: {user_info['department']} | "
            f"License: {user_info.get('license', DEFAULT_LICENSE)} | "
            f"Groups: {', '.join(groups)}"
        )
        log_onboard(user_info["user_id"], detail, cursor)
        print(f"  [+] Onboarding logged in audit_log")

        conn.commit()
        print(f"\\n  Onboarding complete for {user_info['display_name']}.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"  [ERROR] Failed to onboard user: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":

    # Placeholder for onboarding logic:
    # 1. Create user account in 'users' table
    # 2. Assign default license (e.g. M365_E3)
    # 3. Add to security groups based on department
    # 4. Log actions in 'audit_log' table

    test_user = {
        "user_id": "U1112",
        "display_name": "Jane Smith",
        "email": "jane@test2.com",
        "department": "Sales",
        "job_title": "Sales Representative",
        "status": "active",
        "hire_date": datetime.now().strftime("%Y-%m-%d"),
        "manager_email": "sales.manager@company.com)",
        "license": "M365_E3",
    }
    onboard_user(test_user)
