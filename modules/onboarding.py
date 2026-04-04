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
    # ?: execute 메서드는 '리스트'나 '튜플'을 원한다, (email, )는 tuple이라는 python의 데이터형식.
    # type(("test@email.com", )) → <class 'tuple'> (요소가 하나인 튜플)
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


def onboard_user(user_info: dict):
    """
    Onboard a new user based on provided information.

    Args:
        user_info (dict): { "user_id": "U1002", ... (same fields as users table)}
    """

    print(f"  ONBOARDING: {user_info.get('display_name')} ({user_info.get('user_id')})")

    # Step 1 — Validate input data
    errors = validate_new_user(user_info)
    if errors:
        print(f"  [ERROR] Validation failed: {errors}")
        return


if __name__ == "__main__":
    print("[Onboarding] Starting new employee onboarding process...")

    # Placeholder for onboarding logic:
    # 1. Create user account in 'users' table
    # 2. Assign default license (e.g. M365_E3)
    # 3. Add to security groups based on department
    # 4. Log actions in 'audit_log' table

    test_user = {
        "user_id": "U1002",
        "display_name": "Jane Smith",
        "email": "",
        "department": "Sales",
        "job_title": "Sales Representative",
        "status": "active",
        "last_login": None,
        "hire_date": datetime.now().strftime("%Y-%m-%d"),
        "termination_date": None,
        "manager_email": "",
        "license": "M365_E3",
    }
    onboard_user(test_user)
    print("[Onboarding] Onboarding complete.")
