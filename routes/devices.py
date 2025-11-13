"""
Device routes - device configuration and management
"""
from flask import Blueprint, request, jsonify
from services import PLCManager, DeviceService
import logging

logger = logging.getLogger(__name__)

devices_bp = Blueprint('devices', __name__, url_prefix='/api/devices')

def get_plc_manager():
    """Get PLC manager instance from app"""
    from flask import current_app
    return current_app.config.get('plc_manager')


@devices_bp.route('', methods=['GET'])
def get_devices():
    """Get all devices"""
    try:
        plc_manager = get_plc_manager()
        
        devices = DeviceService.get_all_devices()
        device_list = []
        
        for device in devices:
            runtime_status = plc_manager.get_device_status(device.device_id)
            device_dict = device.to_dict()
            
            if runtime_status:
                device_dict.update({
                    'running': runtime_status['running'],
                    'connected': runtime_status['connected'],
                    'last_data': runtime_status['last_data'],
                    'last_error': runtime_status['last_error'],
                    'message_count': runtime_status['message_count'],
                    'last_update': runtime_status['last_update']
                })
            
            device_list.append(device_dict)
        
        return jsonify(device_list)
        
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({'error': str(e)}), 500


@devices_bp.route('', methods=['POST'])
def create_device():
    """Create a new device"""
    try:
        plc_manager = get_plc_manager()
        
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'host']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get or discover tags
        tags = data.get('tags', [])
        if not tags:
            # Auto-discover tags
            try:
                host = data['host']
                slot = int(data.get('slot', 0))
                tags = plc_manager.discover_tags(host, slot)
                
                if not tags:
                    return jsonify({'error': 'No tags discovered from device'}), 400
                    
            except Exception as e:
                return jsonify({'error': f'Failed to discover tags: {str(e)}'}), 500
        
        # Process tags
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        
        # Create device in database
        device = DeviceService.create_device(
            name=data['name'],
            host=data['host'],
            slot=int(data.get('slot', 0)),
            hardware_id=data.get('hardware_id'),
            tags=tags,
            mqtt_topic_prefix=data.get('mqtt_topic_prefix', f"ethernetip/{data['name']}/"),
            mqtt_format=data.get('mqtt_format', 'json'),
            poll_interval=float(data.get('poll_interval', 5.0)),
            enabled=data.get('enabled', True),
            auto_start=data.get('auto_start', True)
        )
        
        # Add to PLC manager
        plc_manager.add_device(
            device_id=device.device_id,
            name=device.name,
            host=device.host,
            slot=device.slot,
            tags=[tag.name for tag in device.tags],
            poll_interval=device.poll_interval,
            hardware_id=device.hardware_id,
            mqtt_format=device.mqtt_format,
            mqtt_topic_prefix=device.mqtt_topic_prefix
        )
        
        # Auto-start if configured
        if device.auto_start:
            plc_manager.start_device(device.device_id)
        
        logger.info(f"Created device: {device.name}")
        
        return jsonify({
            'success': True,
            'device_id': device.device_id,
            'device': device.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating device: {e}")
        return jsonify({'error': str(e)}), 500


@devices_bp.route('/<device_id>', methods=['GET'])
def get_device(device_id):
    """Get a specific device"""
    try:
        plc_manager = get_plc_manager()
        
        device = DeviceService.get_device(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        runtime_status = plc_manager.get_device_status(device_id)
        device_dict = device.to_dict()
        
        if runtime_status:
            device_dict.update({
                'running': runtime_status['running'],
                'connected': runtime_status['connected'],
                'last_data': runtime_status['last_data'],
                'last_error': runtime_status['last_error'],
                'message_count': runtime_status['message_count'],
                'last_update': runtime_status['last_update']
            })
        
        return jsonify(device_dict)
        
    except Exception as e:
        logger.error(f"Error getting device: {e}")
        return jsonify({'error': str(e)}), 500


@devices_bp.route('/<device_id>', methods=['PUT'])
def update_device(device_id):
    """Update a device"""
    try:
        plc_manager = get_plc_manager()
        
        data = request.json
        
        # Stop device if running
        was_running = False
        runtime_status = plc_manager.get_device_status(device_id)
        if runtime_status and runtime_status['running']:
            was_running = True
            plc_manager.stop_device(device_id)
        
        # Update in database
        device = DeviceService.update_device(device_id, **data)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Update PLC manager
        plc_manager.remove_device(device_id)
        plc_manager.add_device(
            device_id=device.device_id,
            name=device.name,
            host=device.host,
            slot=device.slot,
            tags=[tag.name for tag in device.tags],
            poll_interval=device.poll_interval,
            hardware_id=device.hardware_id,
            mqtt_format=device.mqtt_format,
            mqtt_topic_prefix=device.mqtt_topic_prefix
        )
        
        # Restart if it was running
        if was_running:
            plc_manager.start_device(device_id)
        
        logger.info(f"Updated device: {device.name}")
        
        return jsonify({
            'success': True,
            'device': device.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating device: {e}")
        return jsonify({'error': str(e)}), 500


@devices_bp.route('/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Delete a device"""
    try:
        plc_manager = get_plc_manager()
        
        # Remove from PLC manager
        plc_manager.remove_device(device_id)
        
        # Delete from database
        success = DeviceService.delete_device(device_id)
        if not success:
            return jsonify({'error': 'Device not found'}), 404
        
        logger.info(f"Deleted device: {device_id}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        return jsonify({'error': str(e)}), 500


@devices_bp.route('/<device_id>/start', methods=['POST'])
def start_device(device_id):
    """Start a device"""
    try:
        plc_manager = get_plc_manager()
        
        device = DeviceService.get_device(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        success = plc_manager.start_device(device_id)
        if not success:
            return jsonify({'error': 'Failed to start device'}), 400
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error starting device: {e}")
        return jsonify({'error': str(e)}), 500


@devices_bp.route('/<device_id>/stop', methods=['POST'])
def stop_device(device_id):
    """Stop a device"""
    try:
        plc_manager = get_plc_manager()
        
        device = DeviceService.get_device(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        success = plc_manager.stop_device(device_id)
        if not success:
            return jsonify({'error': 'Failed to stop device'}), 400
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error stopping device: {e}")
        return jsonify({'error': str(e)}), 500


@devices_bp.route('/start-all', methods=['POST'])
def start_all():
    """Start all devices"""
    try:
        plc_manager = get_plc_manager()
        
        plc_manager.start_all()
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error starting all devices: {e}")
        return jsonify({'error': str(e)}), 500


@devices_bp.route('/stop-all', methods=['POST'])
def stop_all():
    """Stop all devices"""
    try:
        plc_manager = get_plc_manager()
        
        plc_manager.stop_all()
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error stopping all devices: {e}")
        return jsonify({'error': str(e)}), 500


@devices_bp.route('/discover-tags', methods=['POST'])
def discover_tags():
    """Discover tags from a PLC"""
    try:
        plc_manager = get_plc_manager()
        
        data = request.json
        
        if 'host' not in data:
            return jsonify({'error': 'Host address is required'}), 400
        
        host = data['host']
        slot = int(data.get('slot', 0))
        
        tags = plc_manager.discover_tags(host, slot)
        
        if not tags:
            return jsonify({'error': 'No tags discovered'}), 404
        
        return jsonify({
            'success': True,
            'tags': tags,
            'count': len(tags)
        })
        
    except Exception as e:
        logger.error(f"Error discovering tags: {e}")
        return jsonify({'error': str(e)}), 500
