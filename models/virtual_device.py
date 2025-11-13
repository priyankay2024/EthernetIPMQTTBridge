"""
Virtual Device models - represents virtual child devices mapped to physical parent devices
"""
from datetime import datetime
from . import db


class VirtualDevice(db.Model):
    """Virtual Device mapped to a parent physical device"""
    __tablename__ = 'virtual_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hardware_id = db.Column(db.String(100), nullable=False, unique=True)
    parent_device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent_device = db.relationship('Device', backref='virtual_devices', lazy=True)
    tag_mappings = db.relationship('VirtualDeviceTagMap', backref='virtual_device', 
                                   lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_tags=False):
        """Convert virtual device to dictionary"""
        result = {
            'id': self.id,
            'name': self.name,
            'hardware_id': self.hardware_id,
            'parent_device_id': self.parent_device_id,
            'parent_device_name': self.parent_device.name if self.parent_device else None,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tag_count': self.tag_mappings.count()
        }
        
        if include_tags:
            result['tags'] = [mapping.to_dict() for mapping in self.tag_mappings.all()]
        
        return result
    
    def __repr__(self):
        return f'<VirtualDevice {self.name} (HWID: {self.hardware_id})>'


class VirtualDeviceTagMap(db.Model):
    """Mapping between virtual devices and tags from parent device"""
    __tablename__ = 'virtual_device_tag_map'
    
    id = db.Column(db.Integer, primary_key=True)
    virtual_device_id = db.Column(db.Integer, db.ForeignKey('virtual_devices.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tag = db.relationship('Tag', backref='virtual_mappings', lazy=True)
    
    # Unique constraint to prevent duplicate mappings
    __table_args__ = (
        db.UniqueConstraint('virtual_device_id', 'tag_id', name='unique_virtual_device_tag'),
    )
    
    def to_dict(self):
        """Convert tag mapping to dictionary"""
        return {
            'id': self.id,
            'virtual_device_id': self.virtual_device_id,
            'tag_id': self.tag_id,
            'tag_name': self.tag.name if self.tag else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<VirtualDeviceTagMap vdev={self.virtual_device_id} tag={self.tag_id}>'
