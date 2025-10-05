#!/usr/bin/env python3
import sqlite3
import os

db_path = 'instance/fuetime.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT version_num FROM alembic_version;')
        version = cursor.fetchone()
        print(f'Current alembic version: {version[0] if version else "None"}')
    except Exception as e:
        print(f'Error accessing alembic_version table: {e}')
    conn.close()
else:
    print('Database file not found')
