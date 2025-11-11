from flask import Flask, render_template, jsonify, request
from cpppo.server.enip import client
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
import threading
import time
import json
from datetime import datetime

load_dotenv()

app = Flask(__name__)

class EthernetIPMQTTBridge:
    def __init__(self):
        self.ethernetip_host = os.getenv('ETHERNETIP_HOST', '192.168.1.10')
        self.ethernetip_slot = int(os.getenv('ETHERNETIP_SLOT', '0'))
        self.tags = os.getenv('ETHERNETIP_TAGS', '').split(',')
        self.mqtt_broker = os.getenv('MQTT_BROKER', 'broker.hivemq.com')
        self.mqtt_port = int(os.getenv('MQTT_PORT', '1883'))
        self.mqtt_topic_prefix = os.getenv('MQTT_TOPIC_PREFIX', 'ethernetip/')
        self.mqtt_client_id = os.getenv('MQTT_CLIENT_ID', 'ethernetip_bridge')
        self.poll_interval = float(os.getenv('POLL_INTERVAL', '1.0'))
        
        self.running = False
        self.ethernetip_connected = False
        self.mqtt_connected = False
        self.last_data = {}
        self.last_error = None
        self.message_count = 0
        self.last_update = None
        
        self.mqtt_client = mqtt.Client(client_id=self.mqtt_client_id)
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        
    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.mqtt_connected = True
            self.last_error = None
            print(f"Connected to MQTT broker: {self.mqtt_broker}")
        else:
            self.mqtt_connected = False
            self.last_error = f"MQTT connection failed with code {rc}"
            print(self.last_error)
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        self.mqtt_connected = False
        print("Disconnected from MQTT broker")
        
    def connect_mqtt(self):
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            return True
        except Exception as e:
            self.last_error = f"MQTT connection error: {str(e)}"
            print(self.last_error)
            return False
    
    def read_ethernetip_tags(self):
        try:
            results = {}
            cleaned_tags = [tag.strip() for tag in self.tags if tag.strip()]
            
            if not cleaned_tags:
                self.ethernetip_connected = False
                self.last_error = "No tags configured. Please set ETHERNETIP_TAGS environment variable."
                print(self.last_error)
                return results
            
            print(f"Connecting to EthernetIP device at {self.ethernetip_host}...")
            print(f"Reading tags: {cleaned_tags}")
            
            with client.connector(host=self.ethernetip_host, timeout=5.0) as connection:
                operations = client.parse_operations(cleaned_tags)
                
                for index, descr, op, reply, status, value in connection.synchronous(
                    operations=operations
                ):
                    tag_name = descr.split('=')[0].strip()
                    
                    if not status:
                        results[tag_name] = {'error': 'Read failed'}
                        print(f"Failed to read tag: {tag_name}")
                    else:
                        value_type = type(value).__name__
                        if isinstance(value, list):
                            value_type = f"array[{len(value)}]"
                        
                        results[tag_name] = {'value': value, 'type': value_type}
                        print(f"Successfully read {tag_name}: {value}")
                
                self.ethernetip_connected = True
                self.last_error = None
                return results
                
        except Exception as e:
            self.ethernetip_connected = False
            self.last_error = f"EthernetIP error: {str(e)}"
            print(self.last_error)
            return None
    
    def publish_to_mqtt(self, data):
        if not self.mqtt_connected:
            return
        
        for tag, value in data.items():
            if 'error' in value:
                continue
            
            topic = f"{self.mqtt_topic_prefix}{tag}"
            payload = json.dumps({
                'value': value['value'],
                'type': value['type'],
                'timestamp': datetime.now().isoformat()
            })
            
            try:
                self.mqtt_client.publish(topic, payload, qos=1)
                self.message_count += 1
            except Exception as e:
                self.last_error = f"MQTT publish error: {str(e)}"
                print(self.last_error)
    
    def run(self):
        self.running = True
        self.connect_mqtt()
        mqtt_retry_delay = 5
        last_mqtt_attempt = 0
        
        while self.running:
            if not self.mqtt_connected and (time.time() - last_mqtt_attempt) > mqtt_retry_delay:
                print("Attempting to reconnect to MQTT broker...")
                self.connect_mqtt()
                last_mqtt_attempt = time.time()
                mqtt_retry_delay = min(mqtt_retry_delay * 1.5, 60)
            
            if self.mqtt_connected:
                mqtt_retry_delay = 5
            
            data = self.read_ethernetip_tags()
            
            if data:
                self.last_data = data
                self.publish_to_mqtt(data)
                self.last_update = datetime.now().isoformat()
            
            time.sleep(self.poll_interval)
    
    def start(self):
        if not self.running:
            thread = threading.Thread(target=self.run, daemon=True)
            thread.start()
    
    def stop(self):
        self.running = False
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
    
    def get_status(self):
        return {
            'running': self.running,
            'ethernetip_connected': self.ethernetip_connected,
            'mqtt_connected': self.mqtt_connected,
            'ethernetip_host': self.ethernetip_host,
            'mqtt_broker': self.mqtt_broker,
            'tags': [t.strip() for t in self.tags if t.strip()],
            'last_data': self.last_data,
            'last_error': self.last_error,
            'message_count': self.message_count,
            'last_update': self.last_update,
            'poll_interval': self.poll_interval
        }

bridge = EthernetIPMQTTBridge()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify(bridge.get_status())

@app.route('/api/start', methods=['POST'])
def start_bridge():
    bridge.start()
    return jsonify({'success': True, 'message': 'Bridge started'})

@app.route('/api/stop', methods=['POST'])
def stop_bridge():
    bridge.stop()
    return jsonify({'success': True, 'message': 'Bridge stopped'})

@app.route('/api/config', methods=['GET'])
def config():
    return jsonify(bridge.get_status())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
