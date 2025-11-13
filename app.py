"""
EthernetIP to MQTT Bridge - Main Application
Restructured with clean architecture
"""
from flask import Flask
from flask_socketio import SocketIO
import logging
import os

from config import config
from models import db, Device, MQTTConfig
from services import MQTTClientService, PLCManager, DeviceService
from routes import dashboard_bp, devices_bp, mqtt_bp, tags_bp, virtual_devices_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Load configuration
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize extensions
db.init_app(app)
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='threading')

# Initialize services (will be configured after app initialization)
mqtt_service = None
plc_manager = None
device_service = None

# Register blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(devices_bp)
app.register_blueprint(mqtt_bp)
app.register_blueprint(tags_bp)
app.register_blueprint(virtual_devices_bp)


def initialize_app():
    """Initialize application - database, MQTT, devices"""
    global mqtt_service, plc_manager, device_service
    
    with app.app_context():
        # Initialize services within app context
        mqtt_service = MQTTClientService()
        plc_manager = PLCManager()
        device_service = DeviceService()
        
        # Set service dependencies
        plc_manager.set_services(mqtt_service, device_service, app)
        
        # Store services in app config for access from routes
        app.config['mqtt_service'] = mqtt_service
        app.config['plc_manager'] = plc_manager
        app.config['device_service'] = device_service
        
        # Create database tables
        db.create_all()
        logger.info("Database tables created")
        
        # Load MQTT configuration
        mqtt_config = MQTTConfig.query.filter_by(is_active=True).first()
        
        if not mqtt_config:
            # Create default MQTT configuration
            mqtt_config = MQTTConfig(
                broker=app.config['MQTT_BROKER'],
                port=app.config['MQTT_PORT'],
                client_id=app.config['MQTT_CLIENT_ID'],
                username=app.config.get('MQTT_USERNAME'),
                password=app.config.get('MQTT_PASSWORD'),
                keepalive=app.config['MQTT_KEEPALIVE'],
                is_active=True
            )
            db.session.add(mqtt_config)
            db.session.commit()
            logger.info("Created default MQTT configuration")
        
        # Configure MQTT service
        mqtt_service.configure(
            broker=mqtt_config.broker,
            port=mqtt_config.port,
            client_id=mqtt_config.client_id,
            username=mqtt_config.username,
            password=mqtt_config.password,
            keepalive=mqtt_config.keepalive
        )
        
        # Connect to MQTT
        mqtt_service.connect()
        logger.info("MQTT service connected")
        
        # Load devices from database and start if auto_start is enabled
        devices = Device.query.all()
        logger.info(f"Loading {len(devices)} devices from database")
        
        for device in devices:
            # Add device to PLC manager
            tags = [tag.name for tag in device.tags]
            
            plc_manager.add_device(
                device_id=device.device_id,
                name=device.name,
                host=device.host,
                slot=device.slot,
                tags=tags,
                poll_interval=device.poll_interval,
                hardware_id=device.hardware_id,
                mqtt_format=device.mqtt_format or 'json',
                mqtt_topic_prefix=device.mqtt_topic_prefix
            )
            
            logger.info(f"Loaded device: {device.name}")
            
            # Auto-start if configured
            if device.enabled and device.auto_start:
                plc_manager.start_device(device.device_id)
                logger.info(f"Auto-started device: {device.name}")


# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')


@socketio.on('request_status')
def handle_status_request():
    """Handle status request from client"""
    from flask import jsonify
    from routes.dashboard import get_status
    
    try:
        status = get_status()
        socketio.emit('status_update', status.get_json())
    except Exception as e:
        logger.error(f"Error sending status update: {e}")


# Background task to emit updates
def background_updates():
    """Background task to periodically emit updates to connected clients"""
    import time
    
    # Wait for services to be initialized
    while mqtt_service is None or plc_manager is None:
        time.sleep(0.5)
    
    while True:
        time.sleep(2)  # Update every 2 seconds
        
        try:
            with app.app_context():
                # Get device statuses
                devices = DeviceService.get_all_devices()
                device_updates = []
                
                for device in devices:
                    runtime_status = plc_manager.get_device_status(device.device_id)
                    if runtime_status:
                        device_updates.append(runtime_status)
                
                # Emit to all connected clients
                if device_updates:
                    socketio.emit('device_update', {'devices': device_updates})
                    
        except Exception as e:
            logger.error(f"Error in background updates: {e}")


# Start background updates thread
import threading
updates_thread = threading.Thread(target=background_updates, daemon=True)


@app.before_request
def before_first_request():
    """Initialize before first request"""
    global updates_thread
    if not updates_thread.is_alive():
        updates_thread.start()


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return {'error': 'Not found'}, 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    db.session.rollback()
    return {'error': 'Internal server error'}, 500


if __name__ == '__main__':
    # Initialize the application
    initialize_app()
    
    # Run the application
    logger.info("Starting EthernetIP to MQTT Bridge")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    logger.info(f"Debug mode: {app.config['DEBUG']}")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG'],
        use_reloader=False  # Disable reloader to prevent duplicate processes
    )
