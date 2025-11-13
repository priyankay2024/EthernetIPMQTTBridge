"""
Tag model - represents a PLC tag
"""
from datetime import datetime
from . import db


class Tag(db.Model):
    """PLC Tag"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    data_type = db.Column(db.String(50))
    last_value = db.Column(db.Text)
    last_read = db.Column(db.DateTime)
    read_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on device_id + name
    __table_args__ = (
        db.UniqueConstraint('device_id', 'name', name='unique_device_tag'),
    )
    
    def to_dict(self):
        """Convert tag to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'name': self.name,
            'data_type': self.data_type,
            'last_value': self.last_value,
            'last_read': self.last_read.isoformat() if self.last_read else None,
            'read_count': self.read_count,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Tag {self.name}>'
