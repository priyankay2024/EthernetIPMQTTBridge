"""
Dashboard routes - main dashboard and status overview
"""
from flask import Blueprint, render_template, jsonify
from services import MQTTClientService, PLCManager, DeviceService
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

def get_services():
    """Get service instances from app"""
    from flask import current_app
    return current_app.config.get('mqtt_service'), current_app.config.get('plc_manager')


@dashboard_bp.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@dashboard_bp.route('/api/status')
def get_status():
    """Get overall system status"""
    try:
        mqtt_service, plc_manager = get_services()
        
        # Get MQTT status
        mqtt_status = mqtt_service.get_status()
        
        # Get device statuses
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
            else:
                device_dict.update({
                    'running': False,
                    'connected': False,
                    'last_data': {},
                    'last_error': None,
                    'message_count': 0,
                    'last_update': None
                })
            
            device_list.append(device_dict)
        
        # Count connected devices
        connected_count = sum(1 for d in device_list if d.get('connected', False))
        
        return jsonify({
            'mqtt': mqtt_status,
            'device_count': len(devices),
            'connected_count': connected_count,
            'devices': device_list
        })
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        mqtt_service, plc_manager = get_services()
        
        devices = DeviceService.get_all_devices()
        device_statuses = plc_manager.get_all_status()
        
        total_devices = len(devices)
        running_devices = sum(1 for d in device_statuses if d['running'])
        connected_devices = sum(1 for d in device_statuses if d['connected'])
        total_messages = sum(d.get('message_count', 0) for d in device_statuses)
        
        # Get last communication time
        last_updates = [d.get('last_update') for d in device_statuses if d.get('last_update')]
        last_comm_time = max(last_updates) if last_updates else None
        
        return jsonify({
            'total_devices': total_devices,
            'running_devices': running_devices,
            'connected_devices': connected_devices,
            'total_messages': total_messages,
            'last_comm_time': last_comm_time,
            'mqtt_connected': mqtt_service.connected
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'error': str(e)}), 500
