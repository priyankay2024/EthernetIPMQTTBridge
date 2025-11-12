from flask import Flask, render_template, jsonify, request
# from cpppo.server.enip import client
import ethernetip_simulator as client
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
import threading
import time
import json
from datetime import datetime
import uuid

load_dotenv()

app = Flask(__name__)

class DeviceConnection:
    def __init__(self, device_id, name, host, slot, tags, mqtt_topic_prefix, poll_interval):
        self.device_id = device_id
        self.name = name
        self.host = host
        self.slot = slot
        self.tags = tags
        self.mqtt_topic_prefix = mqtt_topic_prefix
        self.poll_interval = poll_interval
        
        self.running = False
        self.connected = False
        self.last_data = {}
        self.last_error = None
        self.message_count = 0
        self.last_update = None
        self.thread = None

class EthernetIPMQTTBridge:
    def __init__(self):
        self.mqtt_broker = os.getenv('MQTT_BROKER', 'broker.hivemq.com')
        self.mqtt_port = int(os.getenv('MQTT_PORT', '1883'))
        self.mqtt_client_id = os.getenv('MQTT_CLIENT_ID', 'ethernetip_bridge')
        
        self.devices = {}
        self.mqtt_connected = False
        self.mqtt_client = mqtt.Client(client_id=self.mqtt_client_id)
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        self.lock = threading.Lock()
        
    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.mqtt_connected = True
            print(f"Connected to MQTT broker: {self.mqtt_broker}")
        else:
            self.mqtt_connected = False
            print(f"MQTT connection failed with code {rc}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        self.mqtt_connected = False
        print("Disconnected from MQTT broker")
        
    def connect_mqtt(self):
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            return True
        except Exception as e:
            print(f"MQTT connection error: {str(e)}")
            return False
    
    def add_device(self, name, host, slot, tags, mqtt_topic_prefix, poll_interval):
        device_id = str(uuid.uuid4())
        device = DeviceConnection(
            device_id=device_id,
            name=name,
            host=host,
            slot=slot,
            tags=tags,
            mqtt_topic_prefix=mqtt_topic_prefix,
            poll_interval=poll_interval
        )
        with self.lock:
            self.devices[device_id] = device
        return device_id
    
    def remove_device(self, device_id):
        with self.lock:
            if device_id in self.devices:
                device = self.devices[device_id]
                if device.running:
                    self.stop_device(device_id)
                del self.devices[device_id]
                return True
        return False
    
    def update_device(self, device_id, name=None, host=None, slot=None, tags=None, 
                     mqtt_topic_prefix=None, poll_interval=None):
        with self.lock:
            if device_id not in self.devices:
                return False
            
            device = self.devices[device_id]
            was_running = device.running
            
            if was_running:
                self.stop_device(device_id)
            
            if name is not None:
                device.name = name
            if host is not None:
                device.host = host
            if slot is not None:
                device.slot = slot
            if tags is not None:
                device.tags = tags
            if mqtt_topic_prefix is not None:
                device.mqtt_topic_prefix = mqtt_topic_prefix
            if poll_interval is not None:
                device.poll_interval = poll_interval
            
            if was_running:
                self.start_device(device_id)
            
            return True
    
    def read_ethernetip_tags(self, device):
        try:
            results = {}
            cleaned_tags = [tag.strip() for tag in device.tags if tag.strip()]
            
            if not cleaned_tags:
                device.connected = False
                device.last_error = "No tags configured"
                print(f"[{device.name}] No tags configured")
                return results
            
            print(f"[{device.name}] Connecting to {device.host}...")
            
            with client.connector(host=device.host, timeout=5.0) as connection:
                operations = client.parse_operations(cleaned_tags)
                
                for index, descr, op, reply, status, value in connection.synchronous(
                    operations=operations
                ):
                    tag_name = descr.split('=')[0].strip()
                    
                    if not status:
                        results[tag_name] = {'error': 'Read failed'}
                        print(f"[{device.name}] Failed to read tag: {tag_name}")
                    else:
                        value_type = type(value).__name__
                        if isinstance(value, list):
                            value_type = f"array[{len(value)}]"
                        
                        results[tag_name] = {'value': value, 'type': value_type}
                        print(f"[{device.name}] Read {tag_name}: {value}")
                
                device.connected = True
                device.last_error = None
                return results
                
        except Exception as e:
            device.connected = False
            device.last_error = f"EthernetIP error: {str(e)}"
            print(f"[{device.name}] {device.last_error}")
            return None
    
    def publish_to_mqtt(self, device, data):
        if not self.mqtt_connected:
            return
        
        for tag, value in data.items():
            if 'error' in value:
                continue
            
            topic = f"{device.mqtt_topic_prefix}{tag}"
            print(f"[{device.name}] Publishing to MQTT topic: {topic}")
            payload = json.dumps({
                'device_id': device.device_id,
                'device_name': device.name,
                'value': value['value'],
                'type': value['type'],
                'timestamp': datetime.now().isoformat()
            })
            
            try:
                self.mqtt_client.publish(topic, payload, qos=1)
                device.message_count += 1
            except Exception as e:
                device.last_error = f"MQTT publish error: {str(e)}"
                print(f"[{device.name}] {device.last_error}")
    
    def device_loop(self, device_id):
        device = self.devices.get(device_id)
        if not device:
            return
        
        while device.running:
            data = self.read_ethernetip_tags(device)
            
            if data:
                device.last_data = data
                self.publish_to_mqtt(device, data)
                device.last_update = datetime.now().isoformat()
            
            time.sleep(device.poll_interval)
    
    def start_device(self, device_id):
        with self.lock:
            if device_id not in self.devices:
                return False
            
            device = self.devices[device_id]
            if device.running:
                return False
            
            device.running = True
            device.thread = threading.Thread(target=self.device_loop, args=(device_id,), daemon=True)
            device.thread.start()
            return True
    
    def stop_device(self, device_id):
        with self.lock:
            if device_id not in self.devices:
                return False
            
            device = self.devices[device_id]
            device.running = False
            if device.thread:
                device.thread.join(timeout=2)
            return True
    
    def start_all_devices(self):
        if not self.mqtt_connected:
            self.connect_mqtt()
        
        for device_id in list(self.devices.keys()):
            self.start_device(device_id)
    
    def stop_all_devices(self):
        for device_id in list(self.devices.keys()):
            self.stop_device(device_id)
    
    def get_device_status(self, device_id):
        # Note: This function assumes lock is already held by caller
        if device_id not in self.devices:
            return None
        
        device = self.devices[device_id]
        return {
            'device_id': device.device_id,
            'name': device.name,
            'host': device.host,
            'slot': device.slot,
            'tags': device.tags,
            'mqtt_topic_prefix': device.mqtt_topic_prefix,
            'poll_interval': device.poll_interval,
            'running': device.running,
            'connected': device.connected,
            'last_data': device.last_data,
            'last_error': device.last_error,
            'message_count': device.message_count,
            'last_update': device.last_update
        }
    
    def get_all_devices_status(self):
        with self.lock:
            return [self.get_device_status(device_id) for device_id in self.devices.keys()]
    
    def get_status(self):
        with self.lock:
            device_count = len(self.devices)
            devices_list = [self.get_device_status(device_id) for device_id in self.devices.keys()]
        
        return {
            'mqtt_connected': self.mqtt_connected,
            'mqtt_broker': self.mqtt_broker,
            'mqtt_port': self.mqtt_port,
            'device_count': device_count,
            'devices': devices_list
        }

bridge = EthernetIPMQTTBridge()
bridge.connect_mqtt()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify(bridge.get_status())

@app.route('/api/devices', methods=['GET'])
def get_devices():
    return jsonify(bridge.get_all_devices_status())

@app.route('/api/devices', methods=['POST'])
def add_device():
    data = request.json
    
    required_fields = ['name', 'host', 'tags']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Process tags - handle both string and list
    if isinstance(data['tags'], list):
        tags = [tag.strip() for tag in data['tags'] if tag.strip()]
    else:
        tags = [tag.strip() for tag in data['tags'].split(',') if tag.strip()]
    
    if not tags:
        return jsonify({'success': False, 'error': 'At least one tag is required'}), 400
    
    try:
        device_id = bridge.add_device(
            name=data['name'],
            host=data['host'],
            slot=int(data.get('slot', 0)),
            tags=tags,
            mqtt_topic_prefix=data.get('mqtt_topic_prefix', f"ethernetip/{data['name']}/"),
            poll_interval=float(data.get('poll_interval', 5.0))
        )
        
        print(f"Device added successfully: {data['name']} (ID: {device_id})")
        return jsonify({'success': True, 'device_id': device_id})
    except Exception as e:
        print(f"Error adding device: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    status = bridge.get_device_status(device_id)
    if status is None:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    return jsonify(status)

@app.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    data = request.json
    
    success = bridge.update_device(
        device_id=device_id,
        name=data.get('name'),
        host=data.get('host'),
        slot=data.get('slot'),
        tags=data.get('tags'),
        mqtt_topic_prefix=data.get('mqtt_topic_prefix'),
        poll_interval=data.get('poll_interval')
    )
    
    if success:
        return jsonify({'success': True, 'message': 'Device updated'})
    return jsonify({'success': False, 'error': 'Device not found'}), 404

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    success = bridge.remove_device(device_id)
    if success:
        return jsonify({'success': True, 'message': 'Device removed'})
    return jsonify({'success': False, 'error': 'Device not found'}), 404

@app.route('/api/devices/<device_id>/start', methods=['POST'])
def start_device(device_id):
    success = bridge.start_device(device_id)
    if success:
        return jsonify({'success': True, 'message': 'Device started'})
    return jsonify({'success': False, 'error': 'Device not found or already running'}), 400

@app.route('/api/devices/<device_id>/stop', methods=['POST'])
def stop_device(device_id):
    success = bridge.stop_device(device_id)
    if success:
        return jsonify({'success': True, 'message': 'Device stopped'})
    return jsonify({'success': False, 'error': 'Device not found'}), 400

@app.route('/api/start', methods=['POST'])
def start_all():
    bridge.start_all_devices()
    return jsonify({'success': True, 'message': 'All devices started'})

@app.route('/api/stop', methods=['POST'])
def stop_all():
    bridge.stop_all_devices()
    return jsonify({'success': True, 'message': 'All devices stopped'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

