"""
Routes package for EthernetIP to MQTT Bridge
"""
from .dashboard import dashboard_bp
from .devices import devices_bp
from .mqtt import mqtt_bp
from .tags import tags_bp
from .virtual_devices import virtual_devices_bp

__all__ = ['dashboard_bp', 'devices_bp', 'mqtt_bp', 'tags_bp', 'virtual_devices_bp']
