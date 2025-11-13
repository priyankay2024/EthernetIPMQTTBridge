"""
Database migration script to add virtual device tables
Run this script to add virtual_devices and virtual_device_tag_map tables
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import VirtualDevice, VirtualDeviceTagMap

def migrate_database():
    """Add virtual device tables to existing database"""
    with app.app_context():
        print("Creating virtual device tables...")
        
        # Create all tables (will only create missing ones)
        db.create_all()
        
        print("Virtual device tables created successfully!")
        print("- virtual_devices")
        print("- virtual_device_tag_map")
        
        # Verify tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'virtual_devices' in tables and 'virtual_device_tag_map' in tables:
            print("\n✓ Migration completed successfully!")
        else:
            print("\n✗ Warning: Some tables may not have been created")
            print(f"Existing tables: {tables}")

if __name__ == '__main__':
    print("=" * 60)
    print("Virtual Device Migration Script")
    print("=" * 60)
    
    migrate_database()
