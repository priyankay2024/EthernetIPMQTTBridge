"""
MQTT routes - MQTT broker configuration and management
"""
from flask import Blueprint, request, jsonify, current_app
from services import MQTTClientService
from models import db, MQTTConfig
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

mqtt_bp = Blueprint('mqtt', __name__, url_prefix='/api/mqtt')

def get_mqtt_service():
    """Get MQTT service instance from app"""
    return current_app.config.get('mqtt_service')


@mqtt_bp.route('/config', methods=['GET'])
def get_config():
    """Get MQTT configuration"""
    try:
        mqtt_service = get_mqtt_service()
        
        config = MQTTConfig.query.filter_by(is_active=True).first()
        
        if not config:
            # Return default config
            return jsonify({
                'broker': mqtt_service.broker or 'broker.hivemq.com',
                'port': mqtt_service.port or 1883,
                'client_id': mqtt_service.client_id or 'ethernetip_bridge',
                'username': mqtt_service.username or '',
                'has_password': bool(mqtt_service.password),
                'keepalive': mqtt_service.keepalive or 60,
                'connected': mqtt_service.connected
            })
        
        config_dict = config.to_dict()
        config_dict['connected'] = mqtt_service.connected
        
        return jsonify(config_dict)
        
    except Exception as e:
        logger.error(f"Error getting MQTT config: {e}")
        return jsonify({'error': str(e)}), 500


@mqtt_bp.route('/config', methods=['POST', 'PUT'])
def update_config():
    """Update MQTT configuration"""
    try:
        mqtt_service = get_mqtt_service()
        
        data = request.json
        
        # Validate required fields
        if 'broker' not in data:
            return jsonify({'error': 'Broker address is required'}), 400
        
        # Get or create config
        config = MQTTConfig.query.filter_by(is_active=True).first()
        
        if not config:
            config = MQTTConfig()
            db.session.add(config)
        
        # Update config
        config.broker = data['broker']
        config.port = int(data.get('port', 1883))
        config.client_id = data.get('client_id', 'ethernetip_bridge')
        config.username = data.get('username')
        config.keepalive = int(data.get('keepalive', 60))
        
        # Only update password if provided
        if 'password' in data and data['password']:
            config.password = data['password']
        
        config.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Reconnect with new configuration
        mqtt_service.disconnect()
        mqtt_service.configure(
            broker=config.broker,
            port=config.port,
            client_id=config.client_id,
            username=config.username,
            password=config.password,
            keepalive=config.keepalive
        )
        mqtt_service.connect()
        
        logger.info(f"Updated MQTT config: {config.broker}:{config.port}")
        
        return jsonify({
            'success': True,
            'config': config.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating MQTT config: {e}")
        return jsonify({'error': str(e)}), 500


@mqtt_bp.route('/connect', methods=['POST'])
def connect():
    """Connect to MQTT broker"""
    try:
        mqtt_service = get_mqtt_service()
        
        success = mqtt_service.connect()
        
        if success:
            # Update last connected time
            config = MQTTConfig.query.filter_by(is_active=True).first()
            if config:
                config.last_connected = datetime.utcnow()
                db.session.commit()
            
            return jsonify({'success': True, 'message': 'Connected to MQTT broker'})
        else:
            return jsonify({
                'success': False, 
                'error': mqtt_service.last_error or 'Connection failed'
            }), 500
        
    except Exception as e:
        logger.error(f"Error connecting to MQTT: {e}")
        return jsonify({'error': str(e)}), 500


@mqtt_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from MQTT broker"""
    try:
        mqtt_service = get_mqtt_service()
        
        mqtt_service.disconnect()
        return jsonify({'success': True, 'message': 'Disconnected from MQTT broker'})
        
    except Exception as e:
        logger.error(f"Error disconnecting from MQTT: {e}")
        return jsonify({'error': str(e)}), 500


@mqtt_bp.route('/status', methods=['GET'])
def get_status():
    """Get MQTT connection status"""
    try:
        mqtt_service = get_mqtt_service()
        
        status = mqtt_service.get_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting MQTT status: {e}")
        return jsonify({'error': str(e)}), 500


@mqtt_bp.route('/test', methods=['POST'])
def test_connection():
    """Test MQTT connection with provided settings"""
    try:
        data = request.json
        
        if 'broker' not in data:
            return jsonify({'error': 'Broker address is required'}), 400
        
        # Create temporary MQTT client for testing
        import paho.mqtt.client as mqtt
        
        test_client = mqtt.Client(client_id=data.get('client_id', 'test_client'))
        
        if data.get('username') and data.get('password'):
            test_client.username_pw_set(data['username'], data['password'])
        
        connection_result = {'success': False}
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                connection_result['success'] = True
                connection_result['message'] = 'Connection successful'
            else:
                connection_result['error'] = f'Connection failed with code {rc}'
            client.disconnect()
        
        test_client.on_connect = on_connect
        
        broker = data['broker']
        port = int(data.get('port', 1883))
        
        test_client.connect(broker, port, 10)
        test_client.loop_start()
        
        # Wait for connection result
        import time
        time.sleep(2)
        
        test_client.loop_stop()
        
        if connection_result['success']:
            return jsonify(connection_result)
        else:
            return jsonify(connection_result), 500
        
    except Exception as e:
        logger.error(f"Error testing MQTT connection: {e}")
        return jsonify({'error': str(e)}), 500
