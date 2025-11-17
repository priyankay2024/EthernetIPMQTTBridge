"""
MQTT Configuration model - stores MQTT broker settings
"""
from datetime import datetime
from . import db


class MQTTConfig(db.Model):
    """MQTT broker configuration"""
    __tablename__ = 'mqtt_config'
    
    id = db.Column(db.Integer, primary_key=True)
    broker = db.Column(db.String(200), nullable=False)
    port = db.Column(db.Integer, default=1883)
    client_id = db.Column(db.String(100))
    username = db.Column(db.String(100))
    password = db.Column(db.String(200))
    keepalive = db.Column(db.Integer, default=60)
    topic_prefix = db.Column(db.String(200), default='ethernetip/')
    is_active = db.Column(db.Boolean, default=True)
    
    # Connection status (not persisted, updated at runtime)
    last_connected = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert MQTT config to dictionary"""
        return {
            'id': self.id,
            'broker': self.broker,
            'port': self.port,
            'client_id': self.client_id,
            'username': self.username,
            'has_password': bool(self.password),
            'keepalive': self.keepalive,
            'topic_prefix': self.topic_prefix,
            'is_active': self.is_active,
            'last_connected': self.last_connected.isoformat() if self.last_connected else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<MQTTConfig {self.broker}:{self.port}>'
