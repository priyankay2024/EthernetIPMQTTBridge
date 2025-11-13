"""
Virtual Device routes - virtual device configuration and management
"""
from flask import Blueprint, request, jsonify, render_template
from services import VirtualDeviceService, DeviceService, PLCManager
from models import Device, Tag
import logging

logger = logging.getLogger(__name__)

virtual_devices_bp = Blueprint('virtual_devices', __name__, url_prefix='/api/virtual-devices')


def get_plc_manager():
    """Get PLC manager instance from app"""
    from flask import current_app
    return current_app.config.get('plc_manager')


@virtual_devices_bp.route('', methods=['GET'])
def get_virtual_devices():
    """Get all virtual devices with optional search"""
    try:
        plc_manager = get_plc_manager()
        search_text = request.args.get('search', '').lower()
        
        virtual_devices = VirtualDeviceService.get_all_virtual_devices()
        
        result = []
        for vdev in virtual_devices:
            vdev_dict = vdev.to_dict(include_tags=True)
            
            # Add runtime status from parent device
            if vdev.parent_device:
                parent_status = plc_manager.get_device_status(vdev.parent_device.device_id)
                if parent_status:
                    vdev_dict['parent_connected'] = parent_status.get('connected', False)
                    vdev_dict['parent_running'] = parent_status.get('running', False)
                else:
                    vdev_dict['parent_connected'] = False
                    vdev_dict['parent_running'] = False
            
            # Apply search filter if provided
            if search_text:
                vdev_name = vdev.name.lower() if vdev.name else ''
                vdev_hwid = vdev.hardware_id.lower() if vdev.hardware_id else ''
                parent_name = vdev.parent_device.name.lower() if vdev.parent_device and vdev.parent_device.name else ''
                
                if (search_text in vdev_name or 
                    search_text in vdev_hwid or 
                    search_text in parent_name):
                    result.append(vdev_dict)
            else:
                result.append(vdev_dict)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting virtual devices: {e}")
        return jsonify({'error': str(e)}), 500


@virtual_devices_bp.route('/<int:virtual_device_id>', methods=['GET'])
def get_virtual_device(virtual_device_id):
    """Get a specific virtual device"""
    try:
        virtual_device = VirtualDeviceService.get_virtual_device(virtual_device_id)
        if not virtual_device:
            return jsonify({'error': 'Virtual device not found'}), 404
        
        return jsonify(virtual_device.to_dict(include_tags=True))
        
    except Exception as e:
        logger.error(f"Error getting virtual device: {e}")
        return jsonify({'error': str(e)}), 500


@virtual_devices_bp.route('', methods=['POST'])
def create_virtual_device():
    """Create a new virtual device"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'hardware_id', 'parent_device_id', 'tag_ids']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create virtual device
        virtual_device = VirtualDeviceService.create_virtual_device(
            name=data['name'],
            hardware_id=data['hardware_id'],
            parent_device_id=data['parent_device_id'],
            tag_ids=data['tag_ids'],
            enabled=data.get('enabled', True)
        )
        
        logger.info(f"Created virtual device: {virtual_device.name}")
        
        return jsonify({
            'success': True,
            'virtual_device': virtual_device.to_dict(include_tags=True)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating virtual device: {e}")
        return jsonify({'error': str(e)}), 500


@virtual_devices_bp.route('/<int:virtual_device_id>', methods=['PUT'])
def update_virtual_device(virtual_device_id):
    """Update a virtual device"""
    try:
        data = request.json
        
        virtual_device = VirtualDeviceService.update_virtual_device(
            virtual_device_id=virtual_device_id,
            name=data.get('name'),
            hardware_id=data.get('hardware_id'),
            parent_device_id=data.get('parent_device_id'),
            tag_ids=data.get('tag_ids'),
            enabled=data.get('enabled')
        )
        
        logger.info(f"Updated virtual device: {virtual_device.name}")
        
        return jsonify({
            'success': True,
            'virtual_device': virtual_device.to_dict(include_tags=True)
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating virtual device: {e}")
        return jsonify({'error': str(e)}), 500


@virtual_devices_bp.route('/<int:virtual_device_id>', methods=['DELETE'])
def delete_virtual_device(virtual_device_id):
    """Delete a virtual device"""
    try:
        success = VirtualDeviceService.delete_virtual_device(virtual_device_id)
        if not success:
            return jsonify({'error': 'Virtual device not found'}), 404
        
        logger.info(f"Deleted virtual device: {virtual_device_id}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting virtual device: {e}")
        return jsonify({'error': str(e)}), 500


@virtual_devices_bp.route('/tags/<int:parent_device_id>', methods=['GET'])
def get_parent_tags(parent_device_id):
    """Get all tags from a parent device"""
    try:
        device = DeviceService.get_device_by_id(parent_device_id)
        if not device:
            return jsonify({'error': 'Parent device not found'}), 404
        
        tags = Tag.query.filter_by(device_id=parent_device_id).all()
        
        return jsonify({
            'success': True,
            'device_name': device.name,
            'tags': [tag.to_dict() for tag in tags]
        })
        
    except Exception as e:
        logger.error(f"Error getting parent tags: {e}")
        return jsonify({'error': str(e)}), 500


@virtual_devices_bp.route('/start/<int:virtual_device_id>', methods=['POST'])
def start_virtual_device(virtual_device_id):
    """
    Start a virtual device (actually just enables it)
    The parent device must be running for data to flow
    """
    try:
        virtual_device = VirtualDeviceService.update_virtual_device(
            virtual_device_id=virtual_device_id,
            enabled=True
        )
        
        logger.info(f"Started virtual device: {virtual_device.name}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error starting virtual device: {e}")
        return jsonify({'error': str(e)}), 500


@virtual_devices_bp.route('/stop/<int:virtual_device_id>', methods=['POST'])
def stop_virtual_device(virtual_device_id):
    """
    Stop a virtual device (actually just disables it)
    """
    try:
        virtual_device = VirtualDeviceService.update_virtual_device(
            virtual_device_id=virtual_device_id,
            enabled=False
        )
        
        logger.info(f"Stopped virtual device: {virtual_device.name}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error stopping virtual device: {e}")
        return jsonify({'error': str(e)}), 500


# Web route for rendering the virtual devices page
@virtual_devices_bp.route('/page', methods=['GET'])
def virtual_devices_page():
    """Render virtual devices management page"""
    return render_template('virtual_devices.html')
