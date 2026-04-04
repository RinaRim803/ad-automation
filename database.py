import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "ad_simulation.db")


def get_connection():
    """Return a SQLite connection with foreign key support enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # access columns by name: row["email"]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Initialize all tables.

    Schema mirrors a simplified Azure AD / M365 structure:
      users        → user accounts (active / inactive / suspended)
      groups       → security groups (e.g. Sales-Team, VPN-Users)
      user_groups  → many-to-many membership between users and groups
      audit_log    → immutable record of every action taken
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ── users ─────────────────────────────────────────────────────────────
    # Mirrors Azure AD User object fields used in real M365 environments.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id                INTEGER  PRIMARY KEY AUTOINCREMENT,
            user_id           TEXT     NOT NULL UNIQUE,   -- e.g. U1001 (like Azure objectId)
            display_name      TEXT     NOT NULL,
            email             TEXT     NOT NULL UNIQUE,   -- UPN in Azure AD
            department        TEXT     NOT NULL,
            job_title         TEXT,
            status            TEXT     NOT NULL DEFAULT 'active',
                                                          -- active / inactive / suspended
            last_login        TEXT,                       -- ISO date: 2025-01-15
            hire_date         TEXT     NOT NULL,
            termination_date  TEXT,                       -- NULL if still employed
            manager_email     TEXT,
            license           TEXT     NOT NULL DEFAULT 'M365_E3',
            created_at        TEXT     NOT NULL DEFAULT (datetime('now')),
            updated_at        TEXT     NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── groups ────────────────────────────────────────────────────────────
    # Security groups — controls access to resources and license assignment.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id           INTEGER  PRIMARY KEY AUTOINCREMENT,
            group_name   TEXT     NOT NULL UNIQUE,   -- e.g. Sales-Team
            department   TEXT,                        -- auto-assign by department if set
            description  TEXT,
            created_at   TEXT     NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── user_groups ───────────────────────────────────────────────────────
    # Many-to-many: one user can belong to multiple groups.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_groups (
            id          INTEGER  PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT     NOT NULL,
            group_name  TEXT     NOT NULL,
            added_at    TEXT     NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id)    REFERENCES users(user_id)   ON DELETE CASCADE,
            FOREIGN KEY (group_name) REFERENCES groups(group_name) ON DELETE CASCADE,
            UNIQUE (user_id, group_name)   -- prevent duplicate membership
        )
    """)

    # ── audit_log ─────────────────────────────────────────────────────────
    # Immutable log — mirrors Azure AD audit logs / M365 compliance center.
    # Every onboarding, offboarding, group change is recorded here.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER  PRIMARY KEY AUTOINCREMENT,
            action      TEXT     NOT NULL,   -- ONBOARD / OFFBOARD / GROUP_ADD /
                                             -- GROUP_REMOVE / STALE_SUSPENDED
            target_user TEXT     NOT NULL,   -- user_id of affected account
            detail      TEXT,                -- human-readable description
            performed_at TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("[DB] Schema initialized successfully.")


if __name__ == "__main__":
    init_db()