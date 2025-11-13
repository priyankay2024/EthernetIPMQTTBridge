"""
PLC Manager - manages PLC device connections and data polling
"""
import threading
import time
import logging
from datetime import datetime
import uuid

# EthernetIP Client Configuration
# Import simulator by default - change in production
import ethernetip_simulator as client

logger = logging.getLogger(__name__)


class PLCConnection:
    """Represents a single PLC device connection"""
    
    def __init__(self, device_id, name, host, slot, tags, poll_interval, 
                 mqtt_service, device_service, flask_app=None):
        self.device_id = device_id
        self.name = name
        self.host = host
        self.slot = slot
        self.tags = tags
        self.poll_interval = poll_interval
        
        self.mqtt_service = mqtt_service
        self.device_service = device_service
        self.flask_app = flask_app
        
        self.running = False
        self.connected = False
        self.thread = None
        self.last_data = {}
        self.last_error = None
        self.message_count = 0
        self.last_update = None
        
        logger.info(f"PLC Connection created: {name} ({host})")
    
    def start(self):
        """Start polling this device"""
        if self.running:
            logger.warning(f"Device {self.name} is already running")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started polling device: {self.name}")
        return True
    
    def stop(self):
        """Stop polling this device"""
        if not self.running:
            return False
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        
        self.connected = False
        logger.info(f"Stopped polling device: {self.name}")
        return True
    
    def _poll_loop(self):
        """Main polling loop for this device"""
        logger.info(f"Poll loop started for {self.name}")
        
        while self.running:
            try:
                data = self._read_tags()
                
                if data:
                    self.last_data = data
                    self._publish_data(data)
                    self.last_update = datetime.utcnow().isoformat()
                    
                    # Update tag values in database with app context
                    if self.flask_app:
                        try:
                            with self.flask_app.app_context():
                                self.device_service.update_tag_values(self.device_id, data)
                        except Exception as e:
                            logger.warning(f"Failed to update DB for {self.name}: {e}")
                
            except Exception as e:
                self.last_error = str(e)
                logger.error(f"Error in poll loop for {self.name}: {e}")
            
            time.sleep(self.poll_interval)
        
        logger.info(f"Poll loop ended for {self.name}")
    
    def _read_tags(self):
        """Read tags from PLC"""
        try:
            results = {}
            cleaned_tags = [tag.strip() for tag in self.tags if tag.strip()]
            
            if not cleaned_tags:
                self.connected = False
                self.last_error = "No tags configured"
                return results
            
            logger.debug(f"Reading tags from {self.name}: {cleaned_tags}")
            
            with client.connector(host=self.host, timeout=5.0) as connection:
                operations = client.parse_operations(cleaned_tags)
                
                for index, descr, op, reply, status, value in connection.synchronous(
                    operations=operations
                ):
                    tag_name = descr.split('=')[0].strip()
                    
                    if not status:
                        results[tag_name] = {'error': 'Read failed'}
                        logger.warning(f"Failed to read tag {tag_name} from {self.name}")
                    else:
                        value_type = type(value).__name__
                        if isinstance(value, list):
                            value_type = f"array[{len(value)}]"
                        
                        results[tag_name] = {'value': value, 'type': value_type}
                        logger.debug(f"Read {tag_name}: {value}")
                
                self.connected = True
                self.last_error = None
                return results
                
        except Exception as e:
            self.connected = False
            self.last_error = f"Read error: {str(e)}"
            logger.error(f"Error reading from {self.name}: {e}")
            return {}
    
    def _publish_data(self, data):
        """Publish data to MQTT"""
        for tag_name, tag_data in data.items():
            if 'error' in tag_data:
                continue
            
            try:
                self.mqtt_service.publish_device_data(
                    device_id=self.device_id,
                    device_name=self.name,
                    tag_name=tag_name,
                    value=tag_data['value'],
                    data_type=tag_data['type'],
                    topic_prefix=f"ethernetip/{self.name}/"
                )
                self.message_count += 1
                
            except Exception as e:
                logger.error(f"Error publishing data for {self.name}: {e}")
    
    def get_status(self):
        """Get current status of this connection"""
        return {
            'device_id': self.device_id,
            'name': self.name,
            'host': self.host,
            'slot': self.slot,
            'tags': self.tags,
            'poll_interval': self.poll_interval,
            'running': self.running,
            'connected': self.connected,
            'last_data': self.last_data,
            'last_error': self.last_error,
            'message_count': self.message_count,
            'last_update': self.last_update
        }


class PLCManager:
    """
    Manages multiple PLC device connections
    """
    _instance = None
    _lock = threading.Lock()
    
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
        
        self.connections = {}
        self.mqtt_service = None
        self.device_service = None
        self.flask_app = None
        self._initialized = True
        
        logger.info("PLC Manager initialized")
    
    def set_services(self, mqtt_service, device_service, flask_app=None):
        """Set service dependencies"""
        self.mqtt_service = mqtt_service
        self.device_service = device_service
        self.flask_app = flask_app
    
    def add_device(self, device_id, name, host, slot, tags, poll_interval):
        """Add a new device connection"""
        if device_id in self.connections:
            logger.warning(f"Device {device_id} already exists")
            return False
        
        connection = PLCConnection(
            device_id=device_id,
            name=name,
            host=host,
            slot=slot,
            tags=tags,
            poll_interval=poll_interval,
            mqtt_service=self.mqtt_service,
            device_service=self.device_service,
            flask_app=self.flask_app
        )
        
        self.connections[device_id] = connection
        logger.info(f"Added device: {name} ({device_id})")
        return True
    
    def remove_device(self, device_id):
        """Remove a device connection"""
        if device_id not in self.connections:
            return False
        
        connection = self.connections[device_id]
        connection.stop()
        del self.connections[device_id]
        
        logger.info(f"Removed device: {connection.name}")
        return True
    
    def start_device(self, device_id):
        """Start polling a specific device"""
        if device_id not in self.connections:
            return False
        
        return self.connections[device_id].start()
    
    def stop_device(self, device_id):
        """Stop polling a specific device"""
        if device_id not in self.connections:
            return False
        
        return self.connections[device_id].stop()
    
    def start_all(self):
        """Start all device connections"""
        for device_id in list(self.connections.keys()):
            self.start_device(device_id)
        
        logger.info("Started all devices")
    
    def stop_all(self):
        """Stop all device connections"""
        for device_id in list(self.connections.keys()):
            self.stop_device(device_id)
        
        logger.info("Stopped all devices")
    
    def get_device_status(self, device_id):
        """Get status of a specific device"""
        if device_id not in self.connections:
            return None
        
        return self.connections[device_id].get_status()
    
    def get_all_status(self):
        """Get status of all devices"""
        return [conn.get_status() for conn in self.connections.values()]
    
    def discover_tags(self, host, slot=0, timeout=5.0):
        """
        Discover all tags from a PLC device
        
        Args:
            host: PLC IP address
            slot: PLC slot number
            timeout: Connection timeout
            
        Returns:
            list: List of discovered tag names
        """
        try:
            logger.info(f"Discovering tags from {host}:{slot}")
            tags = client.list_all_tags(host, slot, timeout)
            logger.info(f"Discovered {len(tags)} tags from {host}")
            return tags
            
        except Exception as e:
            logger.error(f"Error discovering tags from {host}: {e}")
            raise
