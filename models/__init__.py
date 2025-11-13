"""
Database models for EthernetIP to MQTT Bridge
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .device import Device
from .tag import Tag
from .mqtt_config import MQTTConfig
from .virtual_device import VirtualDevice, VirtualDeviceTagMap

__all__ = ['db', 'Device', 'Tag', 'MQTTConfig', 'VirtualDevice', 'VirtualDeviceTagMap']
