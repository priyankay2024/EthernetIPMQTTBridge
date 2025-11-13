/**
 * EthernetIP to MQTT Bridge - Main JavaScript
 */

// Global variables
let updateInterval;
let discoveredTags = [];
const socket = io();

// Initialize on document ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing application...');
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data for all tabs
    loadDashboard();
    updateDashboard(); // Load dashboard device list
    loadMQTTConfig();
    updateDevicesList(true); // Load devices list on startup
    
    // Don't use polling - rely on Socket.IO for updates
    // updateInterval = setInterval(() => {
    //     updateDashboard();
    //     updateDevicesList();
    //     updateLiveData();
    // }, 2000);
    
    // Setup Socket.IO listeners
    setupSocketIO();
});

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Device form
    document.getElementById('add-device-form').addEventListener('submit', handleAddDevice);
    document.getElementById('discover-tags-btn').addEventListener('click', discoverTags);
    document.getElementById('start-all-devices').addEventListener('click', startAllDevices);
    document.getElementById('stop-all-devices').addEventListener('click', stopAllDevices);
    
    // MQTT form
    document.getElementById('mqtt-config-form').addEventListener('submit', handleMQTTConfig);
    document.getElementById('mqtt-connect-btn').addEventListener('click', connectMQTT);
    document.getElementById('mqtt-disconnect-btn').addEventListener('click', disconnectMQTT);
    document.getElementById('mqtt-test-btn').addEventListener('click', testMQTTConnection);
    
    // Tab changes
    document.querySelectorAll('#sidebar-tabs button').forEach(button => {
        button.addEventListener('shown.bs.tab', handleTabChange);
    });
}

/**
 * Setup Socket.IO event listeners
 */
function setupSocketIO() {
    socket.on('connect', () => {
        console.log('Socket.IO connected');
        // Reload current tab data on connect
        const activeTab = document.querySelector('#sidebar-tabs button.active');
        if (activeTab) {
            handleTabChange({target: activeTab});
        }
    });
    
    socket.on('device_update', (data) => {
        console.log('Device update received:', data);
        // Update only the changed values, not full re-render
        updateDeviceValuesOnly(data.devices);
        updateDashboardDeviceListOnly(data.devices);
        updateDashboardStatsOnly();
    });
    
    socket.on('tag_update', (data) => {
        console.log('Tag update received:', data);
        updateLiveDataValuesOnly(data);
    });
}

/**
 * Handle tab changes
 */
function handleTabChange(event) {
    const tabId = event.target.id;
    console.log('Tab changed:', tabId);
    
    // Only load data on first view or explicit refresh
    // Socket.IO updates will handle real-time changes
    switch(tabId) {
        case 'dashboard-tab':
            loadDashboard();
            break;
        case 'devices-tab':
            // Devices list is already loaded on startup and updated via WebSocket
            // No need to reload unless explicitly requested
            break;
        case 'mqtt-tab':
            // Only load if container is empty
            if (!document.getElementById('mqtt-broker').value) {
                loadMQTTConfig();
            }
            break;
        case 'data-tab':
            updateLiveData();
            break;
        case 'tagmap-tab':
            loadTagMap();
            break;
    }
}

/**
 * Dashboard functions
 */
function loadDashboard() {
    fetch('/api/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('stats-total-devices').textContent = data.total_devices || 0;
            document.getElementById('stats-connected-devices').textContent = data.connected_devices || 0;
            document.getElementById('stats-total-messages').textContent = data.total_messages || 0;
            document.getElementById('stats-last-comm').textContent = data.last_comm_time 
                ? formatDateTime(data.last_comm_time) 
                : 'Never';
            
            updateMQTTStatusNav(data.mqtt_connected);
        })
        .catch(error => console.error('Error loading dashboard:', error));
}

function updateDashboard() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            // Update MQTT status
            updateMQTTStatusNav(data.mqtt.connected);
            
            // Update devices list on dashboard
            const container = document.getElementById('dashboard-devices-list');
            if (!data.devices || data.devices.length === 0) {
                container.innerHTML = '<p class="text-muted text-center py-4">No devices configured</p>';
                return;
            }
            
            let html = '<div class="list-group">';
            data.devices.forEach(device => {
                const statusClass = device.connected ? 'success' : (device.running ? 'warning' : 'secondary');
                const statusText = device.connected ? 'Connected' : (device.running ? 'Connecting' : 'Stopped');
                
                html += `
                    <div class="list-group-item" data-device-id="${device.device_id}">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1">${device.name}</h6>
                                <small class="text-muted">${device.host}</small>
                            </div>
                            <span class="badge bg-${statusClass} device-status-badge">${statusText}</span>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            
            container.innerHTML = html;
        })
        .catch(error => console.error('Error updating dashboard:', error));
}

function updateDashboardStatsOnly() {
    fetch('/api/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            // Only update text content, no DOM manipulation
            const totalDevices = document.getElementById('stats-total-devices');
            const connectedDevices = document.getElementById('stats-connected-devices');
            const totalMessages = document.getElementById('stats-total-messages');
            const lastComm = document.getElementById('stats-last-comm');
            
            if (totalDevices && totalDevices.textContent !== String(data.total_devices || 0)) {
                totalDevices.textContent = data.total_devices || 0;
            }
            if (connectedDevices && connectedDevices.textContent !== String(data.connected_devices || 0)) {
                connectedDevices.textContent = data.connected_devices || 0;
            }
            if (totalMessages && totalMessages.textContent !== String(data.total_messages || 0)) {
                totalMessages.textContent = data.total_messages || 0;
            }
            
            const formattedTime = data.last_comm_time ? formatDateTime(data.last_comm_time) : 'Never';
            if (lastComm && lastComm.textContent !== formattedTime) {
                lastComm.textContent = formattedTime;
            }
            
            updateMQTTStatusNav(data.mqtt_connected);
        })
        .catch(error => console.error('Error updating dashboard stats:', error));
}

function updateDashboardDeviceListOnly(devices) {
    if (!devices || devices.length === 0) return;
    
    const container = document.getElementById('dashboard-devices-list');
    if (!container) return;
    
    devices.forEach(device => {
        const deviceItem = container.querySelector(`[data-device-id="${device.device_id}"]`);
        if (!deviceItem) return; // Device not in list yet
        
        const statusBadge = deviceItem.querySelector('.device-status-badge');
        if (statusBadge) {
            const statusClass = device.connected ? 'success' : (device.running ? 'warning' : 'secondary');
            const statusText = device.connected ? 'Connected' : (device.running ? 'Connecting' : 'Stopped');
            
            if (statusBadge.textContent !== statusText) {
                statusBadge.className = `badge bg-${statusClass} device-status-badge`;
                statusBadge.textContent = statusText;
            }
        }
    });
}

function updateMQTTStatusNav(connected) {
    const statusEl = document.getElementById('mqtt-status-nav');
    if (connected) {
        statusEl.className = 'badge bg-success';
        statusEl.textContent = 'Connected';
    } else {
        statusEl.className = 'badge bg-danger';
        statusEl.textContent = 'Disconnected';
    }
}

/**
 * Device functions
 */
function updateDevicesList(forceRefresh = false) {
    // Only do full refresh if forced or container is empty
    const container = document.getElementById('devices-list');
    if (!forceRefresh && container.children.length > 0) {
        return;
    }
    
    fetch('/api/devices')
        .then(response => response.json())
        .then(devices => {
            if (!devices || devices.length === 0) {
                container.innerHTML = '<p class="text-muted text-center py-4">No devices configured</p>';
                return;
            }
            
            let html = '';
            devices.forEach(device => {
                html += createDeviceCard(device);
            });
            
            container.innerHTML = html;
        })
        .catch(error => console.error('Error updating devices list:', error));
}

function createDeviceCard(device) {
    const statusClass = device.connected ? 'success' : (device.running ? 'warning' : 'secondary');
    const statusText = device.connected ? 'Connected' : (device.running ? 'Connecting' : 'Stopped');
    const tagCount = device.tags ? device.tags.length : 0;
    
    return `
        <div class="card mb-3" data-device-id="${device.device_id}">
            <div class="card-header d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-0">${device.name} <span class="badge bg-${statusClass} device-status-badge">${statusText}</span></h6>
                    <small class="text-muted">${device.host}:${device.slot} | ${tagCount} tags</small>
                </div>
                <div class="btn-group btn-group-sm device-controls">
                    ${device.running 
                        ? `<button class="btn btn-danger device-stop-btn" onclick="stopDevice('${device.device_id}')">
                               <i class="bi bi-stop-fill"></i> Stop
                           </button>`
                        : `<button class="btn btn-success device-start-btn" onclick="startDevice('${device.device_id}')">
                               <i class="bi bi-play-fill"></i> Start
                           </button>`
                    }
                    <button class="btn btn-danger" onclick="deleteDevice('${device.device_id}', '${device.name}')">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <small><strong>MQTT Topic:</strong> ${device.mqtt_topic_prefix}</small><br>
                        <small><strong>Poll Interval:</strong> ${device.poll_interval}s</small><br>
                        <small><strong>Messages:</strong> <span class="device-msg-count">${device.message_count || 0}</span></small>
                    </div>
                    <div class="col-md-6">
                        <small><strong>Last Update:</strong> <span class="device-last-update">${device.last_update ? formatDateTime(device.last_update) : 'Never'}</span></small><br>
                        ${device.last_error ? `<small class="text-danger device-error"><strong>Error:</strong> ${device.last_error}</small>` : '<small class="device-error"></small>'}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function updateDeviceValuesOnly(devices) {
    if (!devices || devices.length === 0) return;
    
    devices.forEach(device => {
        // Look specifically in the devices-list container
        const container = document.getElementById('devices-list');
        if (!container) return;
        
        const card = container.querySelector(`[data-device-id="${device.device_id}"]`);
        if (!card) return; // Card doesn't exist in DOM
        
        // Update status badge
        const statusBadge = card.querySelector('.device-status-badge');
        if (statusBadge) {
            const statusClass = device.connected ? 'success' : (device.running ? 'warning' : 'secondary');
            const statusText = device.connected ? 'Connected' : (device.running ? 'Connecting' : 'Stopped');
            
            if (statusBadge.textContent !== statusText) {
                statusBadge.className = `badge bg-${statusClass} device-status-badge`;
                statusBadge.textContent = statusText;
            }
        }
        
        // Update message count
        const msgCount = card.querySelector('.device-msg-count');
        if (msgCount && device.message_count !== undefined) {
            const newCount = String(device.message_count || 0);
            if (msgCount.textContent !== newCount) {
                msgCount.textContent = newCount;
            }
        }
        
        // Update last update time
        const lastUpdate = card.querySelector('.device-last-update');
        if (lastUpdate && device.last_update) {
            const formattedTime = formatDateTime(device.last_update);
            if (lastUpdate.textContent !== formattedTime) {
                lastUpdate.textContent = formattedTime;
            }
        }
        
        // Update error message
        const errorEl = card.querySelector('.device-error');
        if (errorEl) {
            if (device.last_error) {
                const errorHtml = `<strong>Error:</strong> ${device.last_error}`;
                if (errorEl.innerHTML !== errorHtml) {
                    errorEl.className = 'text-danger device-error';
                    errorEl.innerHTML = errorHtml;
                }
            } else if (errorEl.textContent !== '') {
                errorEl.textContent = '';
                errorEl.className = 'device-error';
            }
        }
        
        // Update control buttons if running state changed
        const controls = card.querySelector('.device-controls');
        if (controls) {
            const hasStopBtn = controls.querySelector('.device-stop-btn') !== null;
            const hasStartBtn = controls.querySelector('.device-start-btn') !== null;
            
            if (device.running && hasStartBtn) {
                // Need to switch to stop button
                controls.querySelector('.device-start-btn').outerHTML = 
                    `<button class="btn btn-danger device-stop-btn" onclick="stopDevice('${device.device_id}')">
                        <i class="bi bi-stop-fill"></i> Stop
                    </button>`;
            } else if (!device.running && hasStopBtn) {
                // Need to switch to start button
                controls.querySelector('.device-stop-btn').outerHTML = 
                    `<button class="btn btn-success device-start-btn" onclick="startDevice('${device.device_id}')">
                        <i class="bi bi-play-fill"></i> Start
                    </button>`;
            }
        }
    });
}

function handleAddDevice(e) {
    e.preventDefault();
    
    const deviceData = {
        name: document.getElementById('device-name').value,
        host: document.getElementById('device-host').value,
        slot: parseInt(document.getElementById('device-slot').value),
        tags: discoveredTags.length > 0 ? discoveredTags : [],
        mqtt_topic_prefix: document.getElementById('device-mqtt-prefix').value || undefined,
        poll_interval: parseFloat(document.getElementById('device-poll-interval').value),
        auto_start: document.getElementById('device-auto-start').checked
    };
    
    fetch('/api/devices', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(deviceData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Device added successfully!');
            document.getElementById('add-device-form').reset();
            discoveredTags = [];
            document.getElementById('discovered-tags-container').style.display = 'none';
            updateDevicesList(true); // Force refresh after adding
            loadDashboard(); // Reload dashboard stats
        } else {
            showAlert('danger', 'Error adding device: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error adding device:', error);
        showAlert('danger', 'Error adding device');
    });
}

function discoverTags() {
    const host = document.getElementById('device-host').value;
    const slot = parseInt(document.getElementById('device-slot').value);
    
    if (!host) {
        showAlert('warning', 'Please enter a host address first');
        return;
    }
    
    const btn = document.getElementById('discover-tags-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Discovering...';
    
    fetch('/api/devices/discover-tags', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({host, slot})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            discoveredTags = data.tags;
            displayDiscoveredTags(data.tags);
            document.getElementById('tag-discovery-status').innerHTML = 
                `<i class="bi bi-check-circle text-success"></i> Discovered ${data.count} tags`;
        } else {
            showAlert('danger', 'Error discovering tags: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error discovering tags:', error);
        showAlert('danger', 'Error discovering tags');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-search"></i> Discover Tags';
    });
}

function displayDiscoveredTags(tags) {
    const container = document.getElementById('discovered-tags-container');
    const list = document.getElementById('discovered-tags-list');
    
    let html = '';
    tags.forEach(tag => {
        html += `<span class="badge bg-success me-1 mb-1">${tag}</span>`;
    });
    
    list.innerHTML = html;
    container.style.display = 'block';
}

function startDevice(deviceId) {
    fetch(`/api/devices/${deviceId}/start`, {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // WebSocket will handle the update
                showAlert('success', 'Device started successfully');
            }
        })
        .catch(error => console.error('Error starting device:', error));
}

function stopDevice(deviceId) {
    fetch(`/api/devices/${deviceId}/stop`, {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // WebSocket will handle the update
                showAlert('success', 'Device stopped successfully');
            }
        })
        .catch(error => console.error('Error stopping device:', error));
}

function deleteDevice(deviceId, deviceName) {
    if (!confirm(`Are you sure you want to delete device "${deviceName}"?`)) {
        return;
    }
    
    fetch(`/api/devices/${deviceId}`, {method: 'DELETE'})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'Device deleted successfully');
                updateDevicesList(true); // Force refresh after deleting
                loadDashboard();
            }
        })
        .catch(error => console.error('Error deleting device:', error));
}

function startAllDevices() {
    fetch('/api/devices/start-all', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'All devices started');
                // WebSocket will handle updates
            }
        })
        .catch(error => console.error('Error starting all devices:', error));
}

function stopAllDevices() {
    fetch('/api/devices/stop-all', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('info', 'All devices stopped');
                // WebSocket will handle updates
            }
        })
        .catch(error => console.error('Error stopping all devices:', error));
}

/**
 * MQTT functions
 */
function loadMQTTConfig() {
    fetch('/api/mqtt/config')
        .then(response => response.json())
        .then(data => {
            document.getElementById('mqtt-broker').value = data.broker || '';
            document.getElementById('mqtt-port').value = data.port || 1883;
            document.getElementById('mqtt-client-id').value = data.client_id || '';
            document.getElementById('mqtt-username').value = data.username || '';
            document.getElementById('mqtt-keepalive').value = data.keepalive || 60;
            
            updateMQTTStatus(data.connected);
            document.getElementById('mqtt-current-broker').textContent = 
                data.broker ? `${data.broker}:${data.port}` : '-';
        })
        .catch(error => console.error('Error loading MQTT config:', error));
}

function handleMQTTConfig(e) {
    e.preventDefault();
    
    const configData = {
        broker: document.getElementById('mqtt-broker').value,
        port: parseInt(document.getElementById('mqtt-port').value),
        client_id: document.getElementById('mqtt-client-id').value,
        username: document.getElementById('mqtt-username').value,
        password: document.getElementById('mqtt-password').value,
        keepalive: parseInt(document.getElementById('mqtt-keepalive').value)
    };
    
    fetch('/api/mqtt/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(configData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'MQTT configuration saved and reconnected');
            loadMQTTConfig();
        } else {
            showAlert('danger', 'Error saving MQTT configuration');
        }
    })
    .catch(error => {
        console.error('Error saving MQTT config:', error);
        showAlert('danger', 'Error saving MQTT configuration');
    });
}

function connectMQTT() {
    fetch('/api/mqtt/connect', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'Connected to MQTT broker');
                loadMQTTConfig();
            } else {
                showAlert('danger', 'Failed to connect: ' + data.error);
            }
        })
        .catch(error => console.error('Error connecting to MQTT:', error));
}

function disconnectMQTT() {
    fetch('/api/mqtt/disconnect', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('info', 'Disconnected from MQTT broker');
                loadMQTTConfig();
            }
        })
        .catch(error => console.error('Error disconnecting from MQTT:', error));
}

function testMQTTConnection() {
    const configData = {
        broker: document.getElementById('mqtt-broker').value,
        port: parseInt(document.getElementById('mqtt-port').value),
        client_id: document.getElementById('mqtt-client-id').value,
        username: document.getElementById('mqtt-username').value,
        password: document.getElementById('mqtt-password').value
    };
    
    const btn = document.getElementById('mqtt-test-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Testing...';
    
    fetch('/api/mqtt/test', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(configData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Connection test successful!');
        } else {
            showAlert('danger', 'Connection test failed: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error testing MQTT connection:', error);
        showAlert('danger', 'Error testing connection');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-check2-circle"></i> Test Connection';
    });
}

function updateMQTTStatus(connected) {
    const statusEl = document.getElementById('mqtt-connection-status');
    if (connected) {
        statusEl.className = 'badge bg-success';
        statusEl.textContent = 'Connected';
    } else {
        statusEl.className = 'badge bg-danger';
        statusEl.textContent = 'Disconnected';
    }
}

/**
 * Live data functions
 */
function updateLiveData() {
    fetch('/api/tags/live')
        .then(response => response.json())
        .then(devices => {
            const container = document.getElementById('live-data-container');
            
            if (!devices || devices.length === 0) {
                container.innerHTML = '<p class="text-muted text-center py-4">No live data available</p>';
                return;
            }
            
            let html = '';
            devices.forEach(device => {
                html += `
                    <div class="card mb-3" data-live-device="${device.device_id}">
                        <div class="card-header bg-primary text-white">
                            <h6 class="mb-0"><i class="bi bi-hdd-rack"></i> ${device.device_name}</h6>
                        </div>
                        <div class="card-body">
                            <div class="row">
                `;
                
                device.tags.forEach(tag => {
                    html += `
                        <div class="col-md-4 mb-3">
                            <div class="tag-item" data-tag-name="${tag.name}">
                                <div class="tag-name">${tag.name}</div>
                                <div class="tag-value">${JSON.stringify(tag.value)}</div>
                                <div class="tag-type">${tag.type}</div>
                            </div>
                        </div>
                    `;
                });
                
                html += `
                            </div>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        })
        .catch(error => console.error('Error updating live data:', error));
}

function updateLiveDataValuesOnly(data) {
    if (!data || !data.devices) return;
    
    data.devices.forEach(device => {
        const deviceCard = document.querySelector(`[data-live-device="${device.device_id}"]`);
        if (!deviceCard || !device.last_data) return;
        
        Object.keys(device.last_data).forEach(tagName => {
            const tagData = device.last_data[tagName];
            if (tagData.error) return;
            
            const tagItem = deviceCard.querySelector(`[data-tag-name="${tagName}"]`);
            if (!tagItem) return;
            
            const valueEl = tagItem.querySelector('.tag-value');
            if (valueEl) {
                const newValue = JSON.stringify(tagData.value);
                if (valueEl.textContent !== newValue) {
                    valueEl.textContent = newValue;
                    // Add a brief animation to show value changed
                    valueEl.classList.add('value-updated');
                    setTimeout(() => valueEl.classList.remove('value-updated'), 300);
                }
            }
        });
    });
}

/**
 * Tag map functions
 */
function loadTagMap() {
    fetch('/api/tags/map')
        .then(response => response.json())
        .then(devices => {
            const container = document.getElementById('tagmap-container');
            
            if (!devices || devices.length === 0) {
                container.innerHTML = '<p class="text-muted text-center py-4">No tags configured</p>';
                return;
            }
            
            let html = '<div class="accordion" id="tagMapAccordion">';
            
            devices.forEach((device, index) => {
                const statusBadge = device.connected 
                    ? '<span class="badge bg-success">Connected</span>'
                    : '<span class="badge bg-secondary">Offline</span>';
                
                html += `
                    <div class="accordion-item">
                        <h2 class="accordion-header" id="heading${index}">
                            <button class="accordion-button ${index === 0 ? '' : 'collapsed'}" type="button" 
                                    data-bs-toggle="collapse" data-bs-target="#collapse${index}">
                                ${device.device_name} ${statusBadge} 
                                <span class="badge bg-info ms-2">${device.tags.length} tags</span>
                            </button>
                        </h2>
                        <div id="collapse${index}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" 
                             data-bs-parent="#tagMapAccordion">
                            <div class="accordion-body">
                                <p><strong>Host:</strong> ${device.host}</p>
                                <table class="table table-sm table-striped">
                                    <thead>
                                        <tr>
                                            <th>Tag Name</th>
                                            <th>Data Type</th>
                                            <th>Last Value</th>
                                            <th>Last Read</th>
                                            <th>Read Count</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                `;
                
                device.tags.forEach(tag => {
                    html += `
                        <tr>
                            <td><code>${tag.name}</code></td>
                            <td>${tag.data_type || '-'}</td>
                            <td>${tag.live_value !== undefined ? JSON.stringify(tag.live_value) : (tag.last_value || '-')}</td>
                            <td>${tag.last_read ? formatDateTime(tag.last_read) : 'Never'}</td>
                            <td>${tag.read_count || 0}</td>
                        </tr>
                    `;
                });
                
                html += `
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            container.innerHTML = html;
        })
        .catch(error => console.error('Error loading tag map:', error));
}

/**
 * Utility functions
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch (e) {
        return dateString;
    }
}

function showAlert(type, message) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
