"""
Virtual Device Service - manages virtual device operations
"""
import logging
from models import db, VirtualDevice, VirtualDeviceTagMap, Device, Tag

logger = logging.getLogger(__name__)


class VirtualDeviceService:
    """Service for managing virtual devices"""
    
    @staticmethod
    def get_all_virtual_devices():
        """Get all virtual devices"""
        try:
            return VirtualDevice.query.all()
        except Exception as e:
            logger.error(f"Error getting virtual devices: {e}")
            return []
    
    @staticmethod
    def get_virtual_device(virtual_device_id):
        """Get a virtual device by ID"""
        try:
            return VirtualDevice.query.get(virtual_device_id)
        except Exception as e:
            logger.error(f"Error getting virtual device {virtual_device_id}: {e}")
            return None
    
    @staticmethod
    def get_virtual_devices_by_parent(parent_device_id):
        """Get all virtual devices for a parent device"""
        try:
            return VirtualDevice.query.filter_by(parent_device_id=parent_device_id).all()
        except Exception as e:
            logger.error(f"Error getting virtual devices for parent {parent_device_id}: {e}")
            return []
    
    @staticmethod
    def create_virtual_device(name, hardware_id, parent_device_id, tag_ids, enabled=True):
        """
        Create a new virtual device
        
        Args:
            name: Virtual device name
            hardware_id: Hardware identifier (HWID)
            parent_device_id: ID of parent physical device
            tag_ids: List of tag IDs to map to this virtual device
            enabled: Whether device is enabled
            
        Returns:
            VirtualDevice: Created virtual device
        """
        try:
            # Validate parent device exists
            parent_device = Device.query.get(parent_device_id)
            if not parent_device:
                raise ValueError(f"Parent device {parent_device_id} not found")
            
            # Check if hardware_id is unique
            existing = VirtualDevice.query.filter_by(hardware_id=hardware_id).first()
            if existing:
                raise ValueError(f"Virtual device with HWID '{hardware_id}' already exists")
            
            # Create virtual device
            virtual_device = VirtualDevice(
                name=name,
                hardware_id=hardware_id,
                parent_device_id=parent_device_id,
                enabled=enabled
            )
            
            db.session.add(virtual_device)
            db.session.flush()  # Get the ID without committing
            
            # Create tag mappings
            for tag_id in tag_ids:
                # Verify tag belongs to parent device
                tag = Tag.query.get(tag_id)
                if tag and tag.device_id == parent_device_id:
                    mapping = VirtualDeviceTagMap(
                        virtual_device_id=virtual_device.id,
                        tag_id=tag_id
                    )
                    db.session.add(mapping)
                else:
                    logger.warning(f"Tag {tag_id} not found or doesn't belong to parent device")
            
            db.session.commit()
            logger.info(f"Created virtual device: {name} (HWID: {hardware_id})")
            
            return virtual_device
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating virtual device: {e}")
            raise
    
    @staticmethod
    def update_virtual_device(virtual_device_id, name=None, hardware_id=None, 
                             parent_device_id=None, tag_ids=None, enabled=None):
        """
        Update a virtual device
        
        Args:
            virtual_device_id: ID of virtual device to update
            name: New name (optional)
            hardware_id: New HWID (optional)
            parent_device_id: New parent device ID (optional)
            tag_ids: New list of tag IDs (optional, will replace existing)
            enabled: New enabled state (optional)
            
        Returns:
            VirtualDevice: Updated virtual device
        """
        try:
            virtual_device = VirtualDevice.query.get(virtual_device_id)
            if not virtual_device:
                raise ValueError(f"Virtual device {virtual_device_id} not found")
            
            # Update fields
            if name is not None:
                virtual_device.name = name
            
            if hardware_id is not None and hardware_id != virtual_device.hardware_id:
                # Check if new hardware_id is unique
                existing = VirtualDevice.query.filter_by(hardware_id=hardware_id).first()
                if existing and existing.id != virtual_device_id:
                    raise ValueError(f"Virtual device with HWID '{hardware_id}' already exists")
                virtual_device.hardware_id = hardware_id
            
            if parent_device_id is not None:
                # Validate new parent device exists
                parent_device = Device.query.get(parent_device_id)
                if not parent_device:
                    raise ValueError(f"Parent device {parent_device_id} not found")
                virtual_device.parent_device_id = parent_device_id
            
            if enabled is not None:
                virtual_device.enabled = enabled
            
            # Update tag mappings if provided
            if tag_ids is not None:
                # Remove existing mappings
                VirtualDeviceTagMap.query.filter_by(
                    virtual_device_id=virtual_device_id
                ).delete()
                
                # Add new mappings
                for tag_id in tag_ids:
                    # Verify tag belongs to parent device
                    tag = Tag.query.get(tag_id)
                    if tag and tag.device_id == virtual_device.parent_device_id:
                        mapping = VirtualDeviceTagMap(
                            virtual_device_id=virtual_device_id,
                            tag_id=tag_id
                        )
                        db.session.add(mapping)
                    else:
                        logger.warning(f"Tag {tag_id} not found or doesn't belong to parent device")
            
            db.session.commit()
            logger.info(f"Updated virtual device: {virtual_device.name}")
            
            return virtual_device
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating virtual device: {e}")
            raise
    
    @staticmethod
    def delete_virtual_device(virtual_device_id):
        """
        Delete a virtual device
        
        Args:
            virtual_device_id: ID of virtual device to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            virtual_device = VirtualDevice.query.get(virtual_device_id)
            if not virtual_device:
                return False
            
            # Cascading delete will remove tag mappings
            db.session.delete(virtual_device)
            db.session.commit()
            
            logger.info(f"Deleted virtual device: {virtual_device.name}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting virtual device: {e}")
            return False
    
    @staticmethod
    def get_virtual_device_tags(virtual_device_id):
        """
        Get all tags mapped to a virtual device
        
        Args:
            virtual_device_id: ID of virtual device
            
        Returns:
            list: List of Tag objects
        """
        try:
            mappings = VirtualDeviceTagMap.query.filter_by(
                virtual_device_id=virtual_device_id
            ).all()
            
            return [mapping.tag for mapping in mappings if mapping.tag]
            
        except Exception as e:
            logger.error(f"Error getting virtual device tags: {e}")
            return []
    
    @staticmethod
    def get_tag_virtual_devices(tag_id):
        """
        Get all virtual devices that have this tag mapped
        
        Args:
            tag_id: ID of tag
            
        Returns:
            list: List of VirtualDevice objects
        """
        try:
            mappings = VirtualDeviceTagMap.query.filter_by(tag_id=tag_id).all()
            return [mapping.virtual_device for mapping in mappings if mapping.virtual_device]
            
        except Exception as e:
            logger.error(f"Error getting tag virtual devices: {e}")
            return []
    
    @staticmethod
    def has_virtual_devices(parent_device_id):
        """
        Check if a parent device has any virtual devices
        
        Args:
            parent_device_id: ID of parent device
            
        Returns:
            bool: True if parent device has virtual devices
        """
        try:
            count = VirtualDevice.query.filter_by(
                parent_device_id=parent_device_id,
                enabled=True
            ).count()
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking virtual devices: {e}")
            return False
