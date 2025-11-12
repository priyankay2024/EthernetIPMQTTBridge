let updateInterval;
let editDeviceModal;

document.addEventListener('DOMContentLoaded', function() {
    editDeviceModal = new bootstrap.Modal(document.getElementById('editDeviceModal'));
    
    document.getElementById('add-device-form').addEventListener('submit', addDevice);
    document.getElementById('save-device-btn').addEventListener('click', saveDeviceChanges);
    document.getElementById('start-all-btn').addEventListener('click', startAllDevices);
    document.getElementById('stop-all-btn').addEventListener('click', stopAllDevices);
    
    updateStatus();
    updateInterval = setInterval(updateStatus, 2000);
});

function updateStatus() {
    console.log('=== updateStatus() CALLED ===');
    console.log('Fetching status from /api/status');
    fetch('/api/status')
        .then(response => {
            console.log('Got response:', response);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Status data received:', data);
            document.getElementById('mqtt-status').textContent = data.mqtt_connected ? 'Connected' : 'Disconnected';
            document.getElementById('mqtt-status').className = data.mqtt_connected ? 'badge bg-success' : 'badge bg-danger';
            document.getElementById('mqtt-broker').textContent = data.mqtt_broker || '-';
            document.getElementById('device-count').textContent = data.device_count || 0;
            
            updateDevicesList(data.devices);
        })
        .catch(error => {
            console.error('Error fetching status:', error);
            // Show error in UI instead of silently failing
            const container = document.getElementById('devices-container');
            if (container && container.innerHTML.includes('No devices configured')) {
                container.innerHTML = `
                    <div class="alert alert-warning" role="alert">
                        <i class="bi bi-exclamation-triangle"></i> 
                        <strong>Connection Error:</strong> Unable to connect to server. 
                        Make sure Flask app is running.
                        <br><small>Error: ${error.message}</small>
                    </div>
                `;
            }
        });
}

function updateDevicesList(devices) {
    const container = document.getElementById('devices-container');
    
    console.log('Updating devices list. Device count:', devices ? devices.length : 0);
    console.log('Devices:', devices);
    
    if (!devices || devices.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="bi bi-inbox" style="font-size: 3rem;"></i>
                <p class="mt-3">No devices configured. Add a device to get started.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    devices.forEach(device => {
        console.log('Creating card for device:', device.name);
        const deviceCard = createDeviceCard(device);
        container.appendChild(deviceCard);
    });
    
    console.log('Devices list updated. Cards created:', devices.length);
}

function createDeviceCard(device) {
    console.log('Creating device card for:', device);
    
    const card = document.createElement('div');
    card.className = 'device-card mb-3';
    
    const statusClass = device.connected ? 'bg-success' : (device.running ? 'bg-warning' : 'bg-secondary');
    const statusText = device.connected ? 'Connected' : (device.running ? 'Connecting...' : 'Stopped');
    
    // Ensure tags is an array
    const tags = Array.isArray(device.tags) ? device.tags : [];
    console.log('Device tags:', tags);
    
    let tagsHtml = '';
    if (device.last_data && Object.keys(device.last_data).length > 0) {
        for (const [tag, info] of Object.entries(device.last_data)) {
            if (info.error) {
                tagsHtml += `
                    <div class="tag-item border-danger">
                        <div class="tag-name">${tag}</div>
                        <div class="text-danger small">Error: ${info.error}</div>
                    </div>
                `;
            } else {
                tagsHtml += `
                    <div class="tag-item">
                        <div class="tag-name">${tag}</div>
                        <div class="tag-value">${JSON.stringify(info.value)}</div>
                        <div class="tag-type">Type: ${info.type}</div>
                    </div>
                `;
            }
        }
    } else {
        tagsHtml = '<p class="text-muted mb-0">No data available</p>';
    }
    
    let errorHtml = '';
    if (device.last_error) {
        errorHtml = `
            <div class="alert alert-danger mb-2" role="alert">
                <small><i class="bi bi-exclamation-triangle"></i> ${device.last_error}</small>
            </div>
        `;
    }
    
    card.innerHTML = `
        <div class="device-header">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h5 class="mb-0">
                        <i class="bi bi-hdd-rack"></i> ${device.name}
                        <span class="badge ${statusClass} ms-2">${statusText}</span>
                    </h5>
                    <small class="text-muted">
                        <i class="bi bi-router"></i> ${device.host} | 
                        <i class="bi bi-clock"></i> Poll: ${device.poll_interval}s
                    </small>
                </div>
                <div class="btn-group" role="group">
                    ${device.running 
                        ? `<button class="btn btn-sm btn-danger" onclick="stopDevice('${device.device_id}')">
                               <i class="bi bi-stop-fill"></i> Stop
                           </button>`
                        : `<button class="btn btn-sm btn-success" onclick="startDevice('${device.device_id}')">
                               <i class="bi bi-play-fill"></i> Start
                           </button>`
                    }
                    <button class="btn btn-sm btn-primary" onclick="editDevice('${device.device_id}')">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteDevice('${device.device_id}', '${device.name}')">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </div>
            </div>
        </div>
        <div class="device-body">
            ${errorHtml}
            <div class="row mb-2">
                <div class="col-md-3"><strong>Status:</strong></div>
                <div class="col-md-9">
                    ${device.running ? '<span class="badge bg-success">Running</span>' : '<span class="badge bg-secondary">Stopped</span>'}
                </div>
            </div>
            <div class="row mb-2">
                <div class="col-md-3"><strong>Messages Sent:</strong></div>
                <div class="col-md-9">${device.message_count}</div>
            </div>
            <div class="row mb-2">
                <div class="col-md-3"><strong>Last Update:</strong></div>
                <div class="col-md-9">${device.last_update || 'Never'}</div>
            </div>
            <div class="row mb-2">
                <div class="col-md-3"><strong>MQTT Topic:</strong></div>
                <div class="col-md-9"><code>${device.mqtt_topic_prefix}</code></div>
            </div>
            <div class="row">
                <div class="col-md-3"><strong>Tags:</strong></div>
                <div class="col-md-9">
                    ${tags.length > 0 
                        ? tags.map(tag => `<span class="badge bg-info me-1">${tag}</span>`).join('') 
                        : '<span class="text-muted">No tags configured</span>'}
                </div>
            </div>
            <hr>
            <h6><i class="bi bi-bar-chart"></i> Latest Tag Values:</h6>
            <div class="tag-values-container">
                ${tagsHtml}
            </div>
        </div>
    `;
    
    console.log('Device card created successfully for:', device.name);
    return card;
}

function addDevice(e) {
    e.preventDefault();
    
    const name = document.getElementById('device-name').value;
    const host = document.getElementById('device-host').value;
    const slot = parseInt(document.getElementById('device-slot').value);
    const tags = document.getElementById('device-tags').value;
    const mqttPrefix = document.getElementById('device-mqtt-prefix').value || `ethernetip/${name}/`;
    const pollInterval = parseFloat(document.getElementById('device-poll-interval').value);
    
    const deviceData = {
        name: name,
        host: host,
        slot: slot,
        tags: tags,
        mqtt_topic_prefix: mqttPrefix,
        poll_interval: pollInterval
    };
    
    console.log('Adding device:', deviceData);
    
    fetch('/api/devices', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(deviceData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('API response:', data);
        if (data.success) {
            console.log('Device added successfully:', data.device_id);
            console.log('About to reset form...');
            try {
                document.getElementById('add-device-form').reset();
                console.log('Form reset complete');
            } catch (err) {
                console.error('Error resetting form:', err);
            }
            
            // Force multiple updates to ensure device appears
            console.log('Calling updateStatus() - attempt 1');
            updateStatus();
            
            console.log('Scheduling updateStatus() - attempt 2 (200ms)');
            setTimeout(() => {
                console.log('Calling updateStatus() - attempt 2');
                updateStatus();
            }, 200);
            
            console.log('Scheduling updateStatus() - attempt 3 (500ms)');
            setTimeout(() => {
                console.log('Calling updateStatus() - attempt 3');
                updateStatus();
            }, 500);
            
            console.log('All updateStatus calls initiated');
        } else {
            console.error('Error adding device:', data.error);
            alert('Error adding device: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error adding device:', error);
        alert('Error adding device: ' + error.message);
    });
}

function startDevice(deviceId) {
    console.log('Starting device:', deviceId);
    fetch(`/api/devices/${deviceId}/start`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log('Start device response:', data);
            if (!data.success) {
                alert('Error starting device: ' + data.error);
            }
            // Immediately update to show the device starting
            setTimeout(() => updateStatus(), 100);
        })
        .catch(error => {
            console.error('Error starting device:', error);
            alert('Error starting device: ' + error.message);
        });
}

function stopDevice(deviceId) {
    console.log('Stopping device:', deviceId);
    fetch(`/api/devices/${deviceId}/stop`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log('Stop device response:', data);
            if (!data.success) {
                alert('Error stopping device: ' + data.error);
            }
            // Immediately update to show the device stopping
            setTimeout(() => updateStatus(), 100);
        })
        .catch(error => {
            console.error('Error stopping device:', error);
            alert('Error stopping device: ' + error.message);
        });
}

function deleteDevice(deviceId, deviceName) {
    if (!confirm(`Are you sure you want to delete device "${deviceName}"?`)) {
        return;
    }
    
    fetch(`/api/devices/${deviceId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStatus();
            } else {
                alert('Error deleting device: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error deleting device:', error);
        });
}

function editDevice(deviceId) {
    fetch(`/api/devices/${deviceId}`)
        .then(response => response.json())
        .then(device => {
            document.getElementById('edit-device-id').value = device.device_id;
            document.getElementById('edit-device-name').value = device.name;
            document.getElementById('edit-device-host').value = device.host;
            document.getElementById('edit-device-slot').value = device.slot;
            document.getElementById('edit-device-tags').value = device.tags.join(',');
            document.getElementById('edit-device-mqtt-prefix').value = device.mqtt_topic_prefix;
            document.getElementById('edit-device-poll-interval').value = device.poll_interval;
            
            editDeviceModal.show();
        })
        .catch(error => {
            console.error('Error loading device:', error);
        });
}

function saveDeviceChanges() {
    const deviceId = document.getElementById('edit-device-id').value;
    const deviceData = {
        name: document.getElementById('edit-device-name').value,
        host: document.getElementById('edit-device-host').value,
        slot: parseInt(document.getElementById('edit-device-slot').value),
        tags: document.getElementById('edit-device-tags').value.split(',').map(t => t.trim()),
        mqtt_topic_prefix: document.getElementById('edit-device-mqtt-prefix').value,
        poll_interval: parseFloat(document.getElementById('edit-device-poll-interval').value)
    };
    
    fetch(`/api/devices/${deviceId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(deviceData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            editDeviceModal.hide();
            updateStatus();
        } else {
            alert('Error updating device: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error updating device:', error);
        alert('Error updating device');
    });
}

function startAllDevices() {
    console.log('Starting all devices...');
    fetch('/api/start', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log('Start all response:', data);
            // Immediately update to show the devices starting
            setTimeout(() => updateStatus(), 100);
        })
        .catch(error => {
            console.error('Error starting all devices:', error);
            alert('Error starting all devices: ' + error.message);
        });
}

function stopAllDevices() {
    console.log('Stopping all devices...');
    fetch('/api/stop', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log('Stop all response:', data);
            // Immediately update to show the devices stopping
            setTimeout(() => updateStatus(), 100);
        })
        .catch(error => {
            console.error('Error stopping all devices:', error);
            alert('Error stopping all devices: ' + error.message);
        });
}

