"""
Database migration script to add new columns to Device table
Run this script to update existing database schema
"""
from app import app, db
from models import Device
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database():
    """Add new columns to Device table if they don't exist"""
    with app.app_context():
        try:
            # Try to add the new columns using raw SQL
            # This is safe because if columns exist, it will just fail silently
            with db.engine.connect() as conn:
                # Add hardware_id column
                try:
                    conn.execute(db.text(
                        "ALTER TABLE devices ADD COLUMN hardware_id VARCHAR(100)"
                    ))
                    conn.commit()
                    logger.info("Added hardware_id column")
                except Exception as e:
                    logger.info(f"hardware_id column might already exist: {e}")
                
                # Add mqtt_format column with default value
                try:
                    conn.execute(db.text(
                        "ALTER TABLE devices ADD COLUMN mqtt_format VARCHAR(20) DEFAULT 'json' NOT NULL"
                    ))
                    conn.commit()
                    logger.info("Added mqtt_format column")
                except Exception as e:
                    logger.info(f"mqtt_format column might already exist: {e}")
            
            # Alternatively, just recreate all tables (will not drop existing data in SQLite)
            db.create_all()
            logger.info("Database schema updated successfully")
            
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            raise


if __name__ == '__main__':
    print("Starting database migration...")
    migrate_database()
    print("Migration complete!")
