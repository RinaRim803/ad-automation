"""
group_sync.py

Synchronizes user security group memberships based on department attribute.

Real-world equivalent:
    Azure AD Dynamic Membership Rules — automatically adds or removes users
    from security groups when their department attribute changes.
Why group sync is needed:
    When an employee transfers departments, their group memberships must be
    updated to reflect the new role. Without sync, the user retains access
    to the old department's resources while missing access to the new ones.
    This creates both a security risk (excessive access) and an operational
    problem (missing access).
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db.database import get_connection
from config import cfg

def sync_user_group(user_id: str, new_department: str) -> bool:
    
    return False 

# Quick test
if __name__ == "__main__":
    from data.seed import run as seed
    import os
    # Reset DB
    db_path = os.path.join(os.path.dirname(__file__), "../db/ad_simulation.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    seed()

    # Onboard a test user into Sales
    from modules.onboarding import onboard_user
    onboard_user({
        "user_id":      "U1011",
        "display_name": "Rina Rim",
        "email":        "rina.rim@company.com",
        "department":   "Sales",
        "hire_date":    "2026-04-01",
        "license":      "M365_E3",
    })

    # Simulate department transfer: Sales → Engineering
    print(f"  SIMULATING DEPT TRANSFER: Sales → Engineering")
    sync_user_group("U1011", "Engineering")
