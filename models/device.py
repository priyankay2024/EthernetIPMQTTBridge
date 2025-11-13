"""
Device model - represents a PLC device configuration
"""
from datetime import datetime
from . import db


class Device(db.Model):
    """PLC Device configuration"""
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    host = db.Column(db.String(100), nullable=False)
    slot = db.Column(db.Integer, default=0)
    hardware_id = db.Column(db.String(100), nullable=True)
    mqtt_topic_prefix = db.Column(db.String(200), nullable=False)
    mqtt_format = db.Column(db.String(20), default='json', nullable=False)  # 'json' or 'string'
    poll_interval = db.Column(db.Float, default=5.0)
    enabled = db.Column(db.Boolean, default=True)
    auto_start = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tags = db.relationship('Tag', backref='device', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert device to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'name': self.name,
            'host': self.host,
            'slot': self.slot,
            'hardware_id': self.hardware_id,
            'mqtt_topic_prefix': self.mqtt_topic_prefix,
            'mqtt_format': self.mqtt_format,
            'poll_interval': self.poll_interval,
            'enabled': self.enabled,
            'auto_start': self.auto_start,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tags': [tag.to_dict() for tag in self.tags.all()]
        }
    
    def __repr__(self):
        return f'<Device {self.name} ({self.host})>'
