import sqlite3

conn = sqlite3.connect('fuetime.db')
cursor = conn.cursor()

# Check for emergency alert tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('device_pairings', 'emergency_alerts')")
tables = cursor.fetchall()

print('\n=== Emergency Alert System Tables ===')
if tables:
    for table in tables:
        print(f'[OK] {table[0]}')
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f'  Columns: {len(columns)}')
        for col in columns:
            print(f'    - {col[1]} ({col[2]})')
        print()
else:
    print('[ERROR] No emergency alert tables found')

conn.close()
print('=== Check Complete ===\n')
