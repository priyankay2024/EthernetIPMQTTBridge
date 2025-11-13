"""
Configuration settings for EthernetIP to MQTT Bridge
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///ethernetip_mqtt.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MQTT settings
    MQTT_BROKER = os.getenv('MQTT_BROKER', 'broker.hivemq.com')
    MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
    MQTT_CLIENT_ID = os.getenv('MQTT_CLIENT_ID', 'ethernetip_bridge')
    MQTT_USERNAME = os.getenv('MQTT_USERNAME', None)
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None)
    MQTT_KEEPALIVE = int(os.getenv('MQTT_KEEPALIVE', '60'))
    
    # PLC settings
    DEFAULT_POLL_INTERVAL = float(os.getenv('DEFAULT_POLL_INTERVAL', '5.0'))
    DEFAULT_CONNECTION_TIMEOUT = float(os.getenv('DEFAULT_CONNECTION_TIMEOUT', '5.0'))
    AUTO_START_DEVICES = os.getenv('AUTO_START_DEVICES', 'False').lower() == 'true'
    
    # WebSocket settings
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = '*'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
