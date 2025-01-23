import sqlite3
import os

def get_db_connection():
    """Connect to the SQLite database only if it exists and configure WAL mode."""
    db_path = '/var/lib/headscale/db.sqlite'  # Updated path to match the volume mapping

    # Check if the database file exists
    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"The database file '{db_path}' does not exist. Please ensure Headscale is running and the volume is mounted correctly."
        )

    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enables column access by name

        # Enable WAL mode
        cursor = conn.execute("PRAGMA journal_mode=WAL;")
        wal_mode = cursor.fetchone()[0]
        if wal_mode.upper() != 'WAL':
            raise RuntimeError(f"Failed to set journal mode to WAL. Current mode: {wal_mode}")

        print("WAL mode enabled successfully.")

        # Set wal_autocheckpoint
        wal_autocheckpoint = 1000  # As per configuration
        cursor = conn.execute(f"PRAGMA wal_autocheckpoint = {wal_autocheckpoint};")
        # Optionally, verify if the setting was applied
        cursor = conn.execute("PRAGMA wal_autocheckpoint;")
        current_autocheckpoint = cursor.fetchone()[0]
        if current_autocheckpoint != wal_autocheckpoint:
            raise RuntimeError(
                f"Failed to set wal_autocheckpoint to {wal_autocheckpoint}. Current value: {current_autocheckpoint}"
            )

        print(f"wal_autocheckpoint set to {current_autocheckpoint} successfully.")

        return conn

    except sqlite3.Error as e:
        # Handle SQLite-specific errors
        raise RuntimeError(f"An error occurred while connecting to the database: {e}")
