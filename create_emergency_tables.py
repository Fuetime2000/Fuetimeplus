"""Create emergency alert tables directly"""
from app import app, db
from models.device_pairing import DevicePairing, EmergencyAlert

print('\n=== Creating Emergency Alert Tables ===')

with app.app_context():
    try:
        # Create tables
        db.create_all()
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print('\nAll tables in database:')
        for table in sorted(tables):
            print(f'  - {table}')
        
        # Check specifically for emergency tables
        emergency_tables = ['device_pairings', 'emergency_alerts']
        print('\nEmergency Alert Tables:')
        for table in emergency_tables:
            if table in tables:
                print(f'  [OK] {table}')
                # Get columns
                columns = inspector.get_columns(table)
                print(f'       Columns: {len(columns)}')
                for col in columns:
                    print(f'         - {col["name"]} ({col["type"]})')
            else:
                print(f'  [ERROR] {table} - NOT FOUND')
        
        print('\n=== Tables Created Successfully ===\n')
        
    except Exception as e:
        print(f'\n[ERROR] Failed to create tables: {str(e)}\n')
        import traceback
        traceback.print_exc()
