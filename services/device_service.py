"""
Device Service - business logic for device management
"""
import uuid
import logging
from datetime import datetime
from models import db, Device, Tag

logger = logging.getLogger(__name__)


class DeviceService:
    """Service layer for device operations"""
    
    @staticmethod
    def create_device(name, host, slot, tags, mqtt_topic_prefix, poll_interval, 
                     enabled=True, auto_start=True):
        """
        Create a new device in the database
        
        Args:
            name: Device name
            host: PLC IP address
            slot: PLC slot number
            tags: List of tag names
            mqtt_topic_prefix: MQTT topic prefix
            poll_interval: Polling interval in seconds
            enabled: Whether device is enabled
            auto_start: Whether to auto-start device
            
        Returns:
            Device: Created device object
        """
        try:
            device_id = str(uuid.uuid4())
            
            device = Device(
                device_id=device_id,
                name=name,
                host=host,
                slot=slot,
                mqtt_topic_prefix=mqtt_topic_prefix,
                poll_interval=poll_interval,
                enabled=enabled,
                auto_start=auto_start
            )
            
            db.session.add(device)
            db.session.flush()  # Get the ID
            
            # Add tags
            for tag_name in tags:
                tag = Tag(
                    device_id=device.id,
                    name=tag_name
                )
                db.session.add(tag)
            
            db.session.commit()
            
            logger.info(f"Created device: {name} with {len(tags)} tags")
            return device
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating device: {e}")
            raise
    
    @staticmethod
    def get_device(device_id):
        """Get device by device_id"""
        return Device.query.filter_by(device_id=device_id).first()
    
    @staticmethod
    def get_device_by_db_id(db_id):
        """Get device by database ID"""
        return Device.query.get(db_id)
    
    @staticmethod
    def get_all_devices():
        """Get all devices"""
        return Device.query.all()
    
    @staticmethod
    def update_device(device_id, **kwargs):
        """
        Update device properties
        
        Args:
            device_id: Device identifier
            **kwargs: Properties to update
            
        Returns:
            Device: Updated device object
        """
        try:
            device = DeviceService.get_device(device_id)
            if not device:
                return None
            
            # Update allowed fields
            allowed_fields = ['name', 'host', 'slot', 'mqtt_topic_prefix', 
                            'poll_interval', 'enabled', 'auto_start']
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    setattr(device, field, value)
            
            # Handle tags separately
            if 'tags' in kwargs and kwargs['tags'] is not None:
                # Delete existing tags
                Tag.query.filter_by(device_id=device.id).delete()
                
                # Add new tags
                for tag_name in kwargs['tags']:
                    tag = Tag(device_id=device.id, name=tag_name)
                    db.session.add(tag)
            
            device.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Updated device: {device.name}")
            return device
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating device: {e}")
            raise
    
    @staticmethod
    def delete_device(device_id):
        """Delete a device"""
        try:
            device = DeviceService.get_device(device_id)
            if not device:
                return False
            
            db.session.delete(device)
            db.session.commit()
            
            logger.info(f"Deleted device: {device.name}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting device: {e}")
            raise
    
    @staticmethod
    def update_tag_values(device_id, tag_data):
        """
        Update tag values after a read operation
        
        Args:
            device_id: Device identifier
            tag_data: Dictionary of tag_name -> {value, type} or {error}
        """
        try:
            device = DeviceService.get_device(device_id)
            if not device:
                return
            
            for tag_name, data in tag_data.items():
                tag = Tag.query.filter_by(
                    device_id=device.id, 
                    name=tag_name
                ).first()
                
                if not tag:
                    # Create tag if it doesn't exist
                    tag = Tag(device_id=device.id, name=tag_name)
                    db.session.add(tag)
                
                if 'error' in data:
                    tag.last_error = data['error']
                    tag.error_count += 1
                else:
                    tag.last_value = str(data['value'])
                    tag.data_type = data['type']
                    tag.last_read = datetime.utcnow()
                    tag.read_count += 1
                    tag.last_error = None
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating tag values: {e}")
    
    @staticmethod
    def get_device_tags(device_id):
        """Get all tags for a device"""
        device = DeviceService.get_device(device_id)
        if not device:
            return []
        
        return Tag.query.filter_by(device_id=device.id).all()
    
    @staticmethod
    def get_all_tags():
        """Get all tags from all devices"""
        return Tag.query.join(Device).all()
