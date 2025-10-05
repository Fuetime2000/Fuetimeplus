#!/usr/bin/env python3
import sqlite3
import os

# Check if backup file exists
backup_path = 'fuetime.db.backup'
if os.path.exists(backup_path):
    print('Checking backup file for problematic revision...')
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute('SELECT version_num FROM alembic_version;')
        version = cursor.fetchone()
        print(f'Backup file alembic version: {version[0] if version else "None"}')
        conn.close()

        # Check if backup contains the problematic revision
        if version and version[0] == 'e2bb962ea704':
            print('Found problematic revision in backup file!')
            print('This backup file should be removed or updated.')
        else:
            print('Backup file does not contain the problematic revision.')
    except Exception as e:
        print(f'Error checking backup file: {e}')
else:
    print('No backup file found.')
