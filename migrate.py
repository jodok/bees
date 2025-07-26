#!/usr/bin/env python3
"""
Database migration helper script.

This script provides two migration methods:
1. Quick migration (drops and recreates all tables) - use for development
2. Alembic migration (preserves data) - use for production

Usage:
    python migrate.py quick    # Drop and recreate all tables
    python migrate.py alembic  # Use Alembic for proper migrations
"""

import sys
import subprocess
from database import migrate as quick_migrate


def main():
    if len(sys.argv) != 2:
        print("Usage: python migrate.py [quick|alembic]")
        print("  quick   - Drop and recreate all tables (loses data)")
        print("  alembic - Use Alembic for proper migrations (preserves data)")
        sys.exit(1)

    method = sys.argv[1].lower()

    if method == "quick":
        print("Running quick migration (drops and recreates all tables)...")
        quick_migrate()
        print("Quick migration completed!")

    elif method == "alembic":
        print("Setting up Alembic migration...")
        try:
            # Create a new migration
            subprocess.run(
                ["alembic", "revision", "--autogenerate", "-m", "Schema update"],
                check=True,
            )
            print(
                "Migration file created. Review it and then run: alembic upgrade head"
            )
        except subprocess.CalledProcessError as e:
            print(f"Error creating migration: {e}")
            sys.exit(1)

    else:
        print("Invalid method. Use 'quick' or 'alembic'")
        sys.exit(1)


if __name__ == "__main__":
    main()
