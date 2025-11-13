"""
MQTT Client Service - manages MQTT connections and publishing
"""
import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)


class MQTTClientService:
    """
    Singleton MQTT client service for publishing device data
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.client = None
        self.connected = False
        self.broker = None
        self.port = None
        self.client_id = None
        self.username = None
        self.password = None
        self.keepalive = 60
        self.message_count = 0
        self.last_error = None
        self._initialized = True
        
        logger.info("MQTT Client Service initialized")
    
    def configure(self, broker, port=1883, client_id='ethernetip_bridge', 
                  username=None, password=None, keepalive=60):
        """Configure MQTT connection parameters"""
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.keepalive = keepalive
        
        logger.info(f"MQTT configured: {broker}:{port}")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            if self.client:
                try:
                    self.client.disconnect()
                except:
                    pass
            
            self.client = mqtt.Client(client_id=self.client_id)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish
            
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            logger.info(f"Connecting to MQTT broker: {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, self.keepalive)
            self.client.loop_start()
            
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"MQTT connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT: {e}")
        
        self.connected = False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.connected = True
            self.last_error = None
            logger.info(f"Connected to MQTT broker: {self.broker}")
        else:
            self.connected = False
            self.last_error = f"Connection failed with code {rc}"
            logger.error(f"MQTT connection failed: {self.last_error}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection: {rc}")
        else:
            logger.info("MQTT disconnected")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for successful publish"""
        self.message_count += 1
    
    def publish(self, topic, payload, qos=1, retain=False):
        """
        Publish message to MQTT broker
        
        Args:
            topic: MQTT topic
            payload: Message payload (dict or string)
            qos: Quality of Service (0, 1, or 2)
            retain: Retain message flag
            
        Returns:
            bool: True if published successfully
        """
        if not self.connected:
            logger.warning("Cannot publish: MQTT not connected")
            return False
        
        try:
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}")
                return True
            else:
                logger.error(f"Publish failed with code {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing to MQTT: {e}")
            return False
    
    def publish_device_data(self, device_id, device_name, tag_data, 
                           topic_prefix, hardware_id=None, mqtt_format='json'):
        """
        Publish device tag data to MQTT based on format
        
        Args:
            device_id: Device identifier
            device_name: Device name
            tag_data: Dictionary of tag_name -> {value, type}
            topic_prefix: MQTT topic prefix
            hardware_id: Hardware identifier (HWID)
            mqtt_format: Format for publishing ('json' or 'string')
            
        Returns:
            bool: True if published successfully
        """
        try:
            if mqtt_format == 'string':
                return self._publish_device_data_string(
                    device_id, device_name, tag_data, topic_prefix, hardware_id
                )
            else:
                return self._publish_device_data_json(
                    device_id, device_name, tag_data, topic_prefix, hardware_id
                )
        except Exception as e:
            logger.error(f"Error publishing device data: {e}")
            return False
    
    def _publish_device_data_json(self, device_id, device_name, tag_data, 
                                   topic_prefix, hardware_id=None):
        """
        Publish all device tags in single JSON format
        Format: {HWID: value, Tags: {tag1: value1, tag2: value2, ...}, Timestamp: time}
        
        Args:
            device_id: Device identifier
            device_name: Device name
            tag_data: Dictionary of tag_name -> {value, type}
            topic_prefix: MQTT topic prefix
            hardware_id: Hardware identifier (HWID)
            
        Returns:
            bool: True if published successfully
        """
        topic = f"{topic_prefix}data"
        timestamp = datetime.utcnow().isoformat()
        
        # Build payload with HWID and Timestamp
        payload = {
            'HWID': hardware_id or device_name,
        }
        
        # Merge tags directly into payload
        for tag_name, data in tag_data.items():
            if 'error' not in data:
                payload[tag_name] = data['value']
        
        # Add timestamp at the end
        payload['Timestamp'] = timestamp
        
        logger.debug(f"Publishing JSON to {topic}: {payload}")
        return self.publish(topic, payload)
    
    def _publish_device_data_string(self, device_id, device_name, tag_data, 
                                     topic_prefix, hardware_id=None):
        """
        Publish all device tags in single string format
        Format: HWID,tag1_value,tag2_value,...,Timestamp
        
        Args:
            device_id: Device identifier
            device_name: Device name
            tag_data: Dictionary of tag_name -> {value, type}
            topic_prefix: MQTT topic prefix
            hardware_id: Hardware identifier (HWID)
            
        Returns:
            bool: True if published successfully
        """
        topic = f"{topic_prefix}data"
        timestamp = datetime.utcnow().isoformat()
        
        # Build string with tag values
        hwid = hardware_id or device_name
        tag_values = []
        
        for tag_name, data in tag_data.items():
            if 'error' not in data:
                tag_values.append(str(data['value']))
        
        # Format: HWID,tag_values,Timestamp
        payload = f"{hwid},{','.join(tag_values)},{timestamp}"
        
        logger.debug(f"Publishing string to {topic}: {payload}")
        return self.publish(topic, payload)
    
    def get_status(self):
        """Get MQTT client status"""
        return {
            'connected': self.connected,
            'broker': self.broker,
            'port': self.port,
            'client_id': self.client_id,
            'message_count': self.message_count,
            'last_error': self.last_error
        }
