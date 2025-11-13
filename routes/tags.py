"""
Tags routes - tag data and tag map management
"""
from flask import Blueprint, jsonify, current_app
from services import DeviceService, PLCManager
from models import Tag, Device
import logging

logger = logging.getLogger(__name__)

tags_bp = Blueprint('tags', __name__, url_prefix='/api/tags')

def get_plc_manager():
    """Get PLC manager instance from app"""
    return current_app.config.get('plc_manager')


@tags_bp.route('', methods=['GET'])
def get_all_tags():
    """Get all tags from all devices"""
    try:
        tags = DeviceService.get_all_tags()
        
        tag_list = []
        for tag in tags:
            tag_dict = tag.to_dict()
            tag_dict['device_name'] = tag.device.name
            tag_list.append(tag_dict)
        
        return jsonify(tag_list)
        
    except Exception as e:
        logger.error(f"Error getting all tags: {e}")
        return jsonify({'error': str(e)}), 500


@tags_bp.route('/device/<device_id>', methods=['GET'])
def get_device_tags(device_id):
    """Get all tags for a specific device"""
    try:
        device = DeviceService.get_device(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        tags = DeviceService.get_device_tags(device_id)
        
        return jsonify([tag.to_dict() for tag in tags])
        
    except Exception as e:
        logger.error(f"Error getting device tags: {e}")
        return jsonify({'error': str(e)}), 500


@tags_bp.route('/map', methods=['GET'])
def get_tag_map():
    """Get tag map grouped by device"""
    try:
        plc_manager = get_plc_manager()
        
        devices = DeviceService.get_all_devices()
        
        tag_map = []
        for device in devices:
            runtime_status = plc_manager.get_device_status(device.device_id)
            
            device_info = {
                'device_id': device.device_id,
                'device_name': device.name,
                'host': device.host,
                'connected': runtime_status['connected'] if runtime_status else False,
                'tags': []
            }
            
            for tag in device.tags:
                tag_info = tag.to_dict()
                
                # Add live data if available
                if runtime_status and tag.name in runtime_status.get('last_data', {}):
                    live_data = runtime_status['last_data'][tag.name]
                    tag_info['live_value'] = live_data.get('value')
                    tag_info['live_type'] = live_data.get('type')
                
                device_info['tags'].append(tag_info)
            
            tag_map.append(device_info)
        
        return jsonify(tag_map)
        
    except Exception as e:
        logger.error(f"Error getting tag map: {e}")
        return jsonify({'error': str(e)}), 500


@tags_bp.route('/live', methods=['GET'])
def get_live_data():
    """Get live tag data from all running devices"""
    try:
        plc_manager = get_plc_manager()
        
        device_statuses = plc_manager.get_all_status()
        
        live_data = []
        for status in device_statuses:
            if status['connected'] and status['last_data']:
                device_data = {
                    'device_id': status['device_id'],
                    'device_name': status['name'],
                    'tags': []
                }
                
                for tag_name, tag_data in status['last_data'].items():
                    if 'error' not in tag_data:
                        device_data['tags'].append({
                            'name': tag_name,
                            'value': tag_data['value'],
                            'type': tag_data['type']
                        })
                
                live_data.append(device_data)
        
        return jsonify(live_data)
        
    except Exception as e:
        logger.error(f"Error getting live data: {e}")
        return jsonify({'error': str(e)}), 500


@tags_bp.route('/device/<device_id>/live', methods=['GET'])
def get_device_live_data(device_id):
    """Get live tag data for a specific device"""
    try:
        plc_manager = get_plc_manager()
        
        runtime_status = plc_manager.get_device_status(device_id)
        
        if not runtime_status:
            return jsonify({'error': 'Device not found or not running'}), 404
        
        tags = []
        if runtime_status['connected'] and runtime_status['last_data']:
            for tag_name, tag_data in runtime_status['last_data'].items():
                if 'error' not in tag_data:
                    tags.append({
                        'name': tag_name,
                        'value': tag_data['value'],
                        'type': tag_data['type']
                    })
        
        return jsonify({
            'device_id': device_id,
            'device_name': runtime_status['name'],
            'connected': runtime_status['connected'],
            'last_update': runtime_status['last_update'],
            'tags': tags
        })
        
    except Exception as e:
        logger.error(f"Error getting device live data: {e}")
        return jsonify({'error': str(e)}), 500
