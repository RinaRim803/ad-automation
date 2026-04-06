# AD Automation — User Lifecycle Management Simulation

## Scenario

Enterprise IT teams managing Microsoft 365 and Azure Active Directory environments
spend significant time on repetitive identity management tasks: provisioning new
accounts, revoking access for departing employees, auditing inactive accounts, and
keeping security group memberships accurate.

Without automation, these tasks are error-prone, slow, and difficult to audit —
creating compliance gaps and security risks.

---

## Problem

| Task | Manual Process Risk |
|---|---|
| Onboarding | Ghost accounts, missed group assignments, no audit trail |
| Offboarding | Forgotten active accounts, retained access after termination |
| Stale accounts | Dormant credentials that can be exploited if undetected |
| Group membership | Incorrect access levels, manual drift over time |

---

## Solution

A Python-based CLI tool that simulates enterprise user lifecycle management,
mirroring the workflows performed in Azure AD / Microsoft 365 environments.

Built as a local simulation using SQLite — replicating the data structures and
operational logic of real identity management systems without requiring a paid
Azure subscription.

### Modules

| Module | Function | Azure AD Equivalent |
|---|---|---|
| `onboarding.py` | Create account, assign groups, log action | New-ADUser + group assignment |
| `offboarding.py` | Deactivate account, remove all groups, log action | Disable-ADAccount + group removal |
| `stale_accounts.py` | Detect and suspend accounts inactive beyond threshold | Azure AD Access Reviews |
| `group_sync.py` | Auto-assign groups based on department attribute | Dynamic Membership Rules |

### Architecture

```
ad-automation/
├── config.json          # Central config: paths, thresholds, group mappings
├── config.py            # Config loader (used by all modules)
├── main.py              # CLI entry point
├── data/
│   ├── users.csv        # Sample HR data (mirrors Workday / BambooHR export)
│   └── seed.py          # One-time DB initialization and data import
├── db/
│   └── database.py      # SQLite schema + connection manager
├── modules/
│   ├── onboarding.py
│   ├── offboarding.py
│   ├── stale_accounts.py
│   └── group_sync.py    # In Progress
└── docs/                # In Progress
    ├── onboarding.md
    ├── offboarding.md
    ├── stale_accounts.md
    └── group_sync.md
```

### Database Schema

```
users           → User accounts (mirrors Azure AD User object)
groups          → Security groups (mirrors Azure AD Security Groups)
user_groups     → Group membership (many-to-many)
audit_log       → Immutable action log (mirrors Azure AD Audit Logs)
```

---

## Result

```bash
# Onboard a new employee
python main.py onboard --user-id U1012 --name "Alex Jung" \
  --email alex.jung@company.com --dept Engineering --hire-date 2026-04-01

# Run stale account detection (90-day threshold)
python main.py stale

# Sync group membership for Sales department
python main.py sync --dept Sales

# Offboard a departing employee
python main.py offboard --user-id U1007
```

All actions are logged to `audit_log` with timestamps, enabling full traceability
of account lifecycle events.

---

## Stack

- **Language**: Python 3.11
- **Database**: SQLite (via `sqlite3` standard library)
- **Config**: JSON-based central configuration
- **Architecture**: Modular — each lifecycle stage is an independent module

---

## Documentation

Each module has a dedicated doc covering the operational reasoning behind it:

- [Onboarding](docs/onboarding.md)
- Offboarding *(in progress)*
- Stale Accounts *(in progress)*
- Group Sync *(in progress)*