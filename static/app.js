/**
 * EthernetIP to MQTT Bridge - Main JavaScript
 */

// Global variables
let updateInterval;
let discoveredTags = [];
let editingDeviceId = null; // Track which device is being edited
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
    
    // Device search
    const deviceSearchInput = document.getElementById('device-search-input');
    if (deviceSearchInput) {
        let deviceSearchTimeout;
        deviceSearchInput.addEventListener('input', (e) => {
            clearTimeout(deviceSearchTimeout);
            deviceSearchTimeout = setTimeout(() => {
                updateDevicesList(true, e.target.value.trim());
            }, 300); // Debounce for 300ms
        });
    }
    
    // Tag map search
    const tagmapSearchInput = document.getElementById('tagmap-search-input');
    if (tagmapSearchInput) {
        let tagmapSearchTimeout;
        tagmapSearchInput.addEventListener('input', (e) => {
            clearTimeout(tagmapSearchTimeout);
            tagmapSearchTimeout = setTimeout(() => {
                displayTagMap(tagMapData, e.target.value.trim());
            }, 300); // Debounce for 300ms
        });
    }
    
    // Live data search
    const livedataSearchInput = document.getElementById('livedata-search-input');
    if (livedataSearchInput) {
        let livedataSearchTimeout;
        livedataSearchInput.addEventListener('input', (e) => {
            clearTimeout(livedataSearchTimeout);
            livedataSearchTimeout = setTimeout(() => {
                displayLiveData(liveDataCache, e.target.value.trim());
            }, 300); // Debounce for 300ms
        });
    }
    
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
        updateLiveDataValuesOnly(data.devices);
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
        case 'virtual-devices-tab':
            loadVirtualDevices();
            loadParentDeviceOptions();
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
            document.getElementById('stats-virtual-devices').textContent = data.total_virtual_devices || 0;
            document.getElementById('stats-connected-devices').textContent = data.connected_devices || 0;
            document.getElementById('stats-total-messages').textContent = data.total_messages || 0;
            
            const lastCommEl = document.getElementById('stats-last-comm');
            if (lastCommEl) {
                lastCommEl.textContent = data.last_comm_time ? formatDateTime(data.last_comm_time) : 'Never';
            }
            
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
function updateDevicesList(forceRefresh = false, searchText = '') {
    // Only do full refresh if forced or container is empty
    const container = document.getElementById('devices-list');
    if (!forceRefresh && container.children.length > 0 && !searchText) {
        return;
    }
    
    const url = searchText ? `/api/devices?search=${encodeURIComponent(searchText)}` : '/api/devices';
    
    fetch(url)
        .then(response => response.json())
        .then(devices => {
            if (!devices || devices.length === 0) {
                container.innerHTML = searchText 
                    ? '<p class="text-muted text-center py-4">No devices found matching your search</p>'
                    : '<p class="text-muted text-center py-4">No devices configured</p>';
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
                    <button class="btn btn-warning" onclick="editDevice('${device.device_id}')">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    <button class="btn btn-danger" onclick="deleteDevice('${device.device_id}', '${device.name}')">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <small><strong>Hardware ID (HWID):</strong> ${device.hardware_id || 'Not set'}</small><br>
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
    
    // Get selected MQTT format
    const mqttFormat = document.querySelector('input[name="mqtt-format"]:checked').value;
    
    const deviceData = {
        name: document.getElementById('device-name').value,
        host: document.getElementById('device-host').value,
        slot: parseInt(document.getElementById('device-slot').value),
        hardware_id: document.getElementById('device-hardware-id').value || undefined,
        tags: discoveredTags.length > 0 ? discoveredTags : [],
        mqtt_topic_prefix: document.getElementById('device-mqtt-prefix').value || undefined,
        mqtt_format: mqttFormat,
        poll_interval: parseFloat(document.getElementById('device-poll-interval').value),
        auto_start: document.getElementById('device-auto-start').checked
    };
    
    // Check if we're in edit mode
    const isEditMode = editingDeviceId !== null;
    const url = isEditMode ? `/api/devices/${editingDeviceId}` : '/api/devices';
    const method = isEditMode ? 'PUT' : 'POST';
    const successMessage = isEditMode ? 'Device updated successfully!' : 'Device added successfully!';
    
    fetch(url, {
        method: method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(deviceData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', successMessage);
            resetDeviceForm();
            updateDevicesList(true); // Force refresh
            loadDashboard(); // Reload dashboard stats
        } else {
            showAlert('danger', `Error ${isEditMode ? 'updating' : 'adding'} device: ` + data.error);
        }
    })
    .catch(error => {
        console.error(`Error ${isEditMode ? 'updating' : 'adding'} device:`, error);
        showAlert('danger', `Error ${isEditMode ? 'updating' : 'adding'} device`);
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

function editDevice(deviceId) {
    // Fetch device details
    fetch(`/api/devices/${deviceId}`)
        .then(response => response.json())
        .then(device => {
            // Populate form with device data
            document.getElementById('device-name').value = device.name;
            document.getElementById('device-host').value = device.host;
            document.getElementById('device-slot').value = device.slot;
            document.getElementById('device-hardware-id').value = device.hardware_id || '';
            document.getElementById('device-mqtt-prefix').value = device.mqtt_topic_prefix;
            document.getElementById('device-poll-interval').value = device.poll_interval;
            document.getElementById('device-auto-start').checked = device.auto_start;
            
            // Set MQTT format radio button
            const formatRadio = document.getElementById(device.mqtt_format === 'string' ? 'format-string' : 'format-json');
            if (formatRadio) formatRadio.checked = true;
            
            // Store tags
            discoveredTags = device.tags.map(tag => tag.name);
            if (discoveredTags.length > 0) {
                displayDiscoveredTags(discoveredTags);
                document.getElementById('tag-discovery-status').innerHTML = 
                    `<i class="bi bi-info-circle text-info"></i> ${discoveredTags.length} tags loaded`;
            }
            
            // Set edit mode
            editingDeviceId = deviceId;
            
            // Update form UI to show edit mode
            const formHeader = document.querySelector('#devices-view .card-header h5');
            formHeader.innerHTML = '<i class="bi bi-pencil-square"></i> Edit Device';
            formHeader.parentElement.classList.remove('bg-success');
            formHeader.parentElement.classList.add('bg-warning');
            
            const submitBtn = document.querySelector('#add-device-form button[type="submit"]');
            submitBtn.innerHTML = '<i class="bi bi-check-lg"></i> Update Device';
            submitBtn.className = 'btn btn-warning w-100';
            
            // Add cancel button if it doesn't exist
            if (!document.getElementById('cancel-edit-btn')) {
                const cancelBtn = document.createElement('button');
                cancelBtn.type = 'button';
                cancelBtn.id = 'cancel-edit-btn';
                cancelBtn.className = 'btn btn-secondary w-100 mt-2';
                cancelBtn.innerHTML = '<i class="bi bi-x-lg"></i> Cancel';
                cancelBtn.onclick = resetDeviceForm;
                submitBtn.parentElement.appendChild(cancelBtn);
            }
            
            // Scroll to form
            document.querySelector('#devices-view .card').scrollIntoView({ behavior: 'smooth', block: 'start' });
            
            showAlert('info', `Editing device: ${device.name}`);
        })
        .catch(error => {
            console.error('Error loading device:', error);
            showAlert('danger', 'Error loading device details');
        });
}

function resetDeviceForm() {
    // Reset form
    document.getElementById('add-device-form').reset();
    
    // Clear edit mode
    editingDeviceId = null;
    discoveredTags = [];
    document.getElementById('discovered-tags-container').style.display = 'none';
    document.getElementById('tag-discovery-status').innerHTML = 'Auto-discover tags from device';
    
    // Reset form UI
    const formHeader = document.querySelector('#devices-view .card-header h5');
    formHeader.innerHTML = '<i class="bi bi-plus-circle"></i> Add New Device';
    formHeader.parentElement.classList.remove('bg-warning');
    formHeader.parentElement.classList.add('bg-success');
    
    const submitBtn = document.querySelector('#add-device-form button[type="submit"]');
    submitBtn.innerHTML = '<i class="bi bi-plus-lg"></i> Add Device';
    submitBtn.className = 'btn btn-success w-100';
    
    // Remove cancel button
    const cancelBtn = document.getElementById('cancel-edit-btn');
    if (cancelBtn) {
        cancelBtn.remove();
    }
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
// Store live data for filtering
let liveDataCache = [];

function updateLiveData() {
    fetch('/api/tags/live')
        .then(response => response.json())
        .then(devices => {
            liveDataCache = devices;
            displayLiveData(devices);
        })
        .catch(error => console.error('Error updating live data:', error));
}

function displayLiveData(devices, searchText = '') {
    const container = document.getElementById('live-data-container');
    
    if (!devices || devices.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-4">No live data available</p>';
        return;
    }
    
    // Filter devices and tags based on search text
    let filteredDevices = devices;
    if (searchText) {
        const search = searchText.toLowerCase();
        filteredDevices = devices.map(device => {
            // Check if device name, HWID, or host matches
            const deviceMatches = device.device_name.toLowerCase().includes(search) ||
                                (device.hardware_id && device.hardware_id.toLowerCase().includes(search));
            
            // Filter tags that match the search
            const filteredTags = device.tags.filter(tag => 
                tag.name.toLowerCase().includes(search) ||
                (tag.type && tag.type.toLowerCase().includes(search)) ||
                (tag.value && JSON.stringify(tag.value).toLowerCase().includes(search))
            );
            
            // Include device if it matches OR has matching tags
            if (deviceMatches || filteredTags.length > 0) {
                return {
                    ...device,
                    tags: filteredTags.length > 0 ? filteredTags : device.tags
                };
            }
            return null;
        }).filter(device => device !== null);
    }
    
    if (filteredDevices.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-4">No matching devices or tags found</p>';
        return;
    }
    
    let html = '<div class="accordion" id="liveDataAccordion">';
    
    filteredDevices.forEach((device, index) => {
        const statusBadge = device.connected 
            ? '<span class="badge bg-success">Connected</span>'
            : '<span class="badge bg-secondary">Offline</span>';
        
        const hwidText = device.hardware_id ? `<span class="text-muted ms-2">(${device.hardware_id})</span>` : '';
        
        html += `
            <div class="accordion-item" data-live-device="${device.device_id}">
                <h2 class="accordion-header" id="liveHeading${index}">
                    <button class="accordion-button collapsed" type="button" 
                            data-bs-toggle="collapse" data-bs-target="#liveCollapse${index}">
                        <i class="bi bi-hdd-rack me-2"></i> ${device.device_name} ${hwidText} ${statusBadge} 
                        <span class="badge bg-info ms-2">${device.tags.length} tags</span>
                    </button>
                </h2>
                <div id="liveCollapse${index}" class="accordion-collapse collapse" 
                     data-bs-parent="#liveDataAccordion">
                    <div class="accordion-body">
                        <div class="table-responsive">
                            <table class="table table-sm table-striped table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Tag Name</th>
                                        <th>Value</th>
                                        <th>Data Type</th>
                                    </tr>
                                </thead>
                                <tbody>
            `;
        
        device.tags.forEach(tag => {
            html += `
                <tr data-tag-name="${tag.name}">
                    <td><code>${tag.name}</code></td>
                    <td class="tag-value fw-bold text-primary">${JSON.stringify(tag.value)}</td>
                    <td><span class="badge bg-secondary">${tag.type}</span></td>
                </tr>
            `;
        });
        
        html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

function updateLiveDataValuesOnly(devices) {
    if (!devices || !Array.isArray(devices)) {
        // Handle if data is wrapped in an object
        if (devices && devices.devices) {
            devices = devices.devices;
        } else {
            return;
        }
    }
    
    devices.forEach(device => {
        const deviceSection = document.querySelector(`[data-live-device="${device.device_id}"]`);
        if (!deviceSection) return;
        
        // Update status badge in accordion header
        const accordionButton = deviceSection.querySelector('.accordion-button');
        if (accordionButton) {
            // Find and update status badge
            const existingBadge = accordionButton.querySelector('.badge.bg-success, .badge.bg-secondary');
            if (existingBadge) {
                const newStatusClass = device.connected ? 'bg-success' : 'bg-secondary';
                const newStatusText = device.connected ? 'Connected' : 'Offline';
                
                if (!existingBadge.classList.contains(newStatusClass)) {
                    existingBadge.className = `badge ${newStatusClass}`;
                    existingBadge.textContent = newStatusText;
                }
            }
        }
        
        // Update tag values if last_data is available
        if (!device.last_data) return;
        
        Object.keys(device.last_data).forEach(tagName => {
            const tagData = device.last_data[tagName];
            if (tagData.error) return;
            
            const tagRow = deviceSection.querySelector(`[data-tag-name="${tagName}"]`);
            if (!tagRow) return;
            
            const valueEl = tagRow.querySelector('.tag-value');
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
// Store tag map data for filtering
let tagMapData = [];

function loadTagMap() {
    fetch('/api/tags/map')
        .then(response => response.json())
        .then(devices => {
            tagMapData = devices;
            displayTagMap(devices);
        })
        .catch(error => console.error('Error loading tag map:', error));
}

function displayTagMap(devices, searchText = '') {
    const container = document.getElementById('tagmap-container');
    
    if (!devices || devices.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-4">No tags configured</p>';
        return;
    }
    
    // Filter devices and tags based on search text
    let filteredDevices = devices;
    if (searchText) {
        const search = searchText.toLowerCase();
        filteredDevices = devices.map(device => {
            // Check if device name, HWID, or host matches
            const deviceMatches = device.device_name.toLowerCase().includes(search) ||
                                (device.hardware_id && device.hardware_id.toLowerCase().includes(search)) ||
                                device.host.toLowerCase().includes(search);
            
            // Filter tags that match the search
            const filteredTags = device.tags.filter(tag => 
                tag.name.toLowerCase().includes(search) ||
                (tag.data_type && tag.data_type.toLowerCase().includes(search))
            );
            
            // Include device if it matches OR has matching tags
            if (deviceMatches || filteredTags.length > 0) {
                return {
                    ...device,
                    tags: filteredTags.length > 0 ? filteredTags : device.tags
                };
            }
            return null;
        }).filter(device => device !== null);
    }
    
    if (filteredDevices.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-4">No matching devices or tags found</p>';
        return;
    }
    
    let html = '<div class="accordion" id="tagMapAccordion">';
    
    filteredDevices.forEach((device, index) => {
        const statusBadge = device.connected 
            ? '<span class="badge bg-success">Connected</span>'
            : '<span class="badge bg-secondary">Offline</span>';
        
        const hwidText = device.hardware_id ? `<span class="text-muted ms-2">(${device.hardware_id})</span>` : '';
        
        html += `
            <div class="accordion-item">
                <h2 class="accordion-header" id="heading${index}">
                    <button class="accordion-button collapsed" type="button" 
                            data-bs-toggle="collapse" data-bs-target="#collapse${index}">
                        ${device.device_name}  ${hwidText}  ${statusBadge} 
                        <span class="badge bg-info ms-2">${device.tags.length} tags</span>
                    </button>
                </h2>
                <div id="collapse${index}" class="accordion-collapse collapse" 
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

/**
 * ========================================================================
 * VIRTUAL DEVICE MANAGEMENT
 * ========================================================================
 */

// Global variables for virtual devices
let editingVirtualDeviceId = null;
let selectedTags = new Set();
let parentDeviceTags = [];

// Initialize virtual device event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Add virtual device event listeners
    const vdevForm = document.getElementById('add-virtual-device-form');
    if (vdevForm) {
        vdevForm.addEventListener('submit', handleAddVirtualDevice);
    }
    
    const parentSelect = document.getElementById('vdev-parent-device');
    if (parentSelect) {
        parentSelect.addEventListener('change', handleParentDeviceChange);
        parentSelect.addEventListener('click', function(e) {
            if (e.target.tagName === 'OPTION' && e.target.value) {
                handleParentDeviceChange({target: parentSelect});
            }
        });
    }
    
    const parentDeviceSearch = document.getElementById('vdev-parent-device-search');
    if (parentDeviceSearch) {
        parentDeviceSearch.addEventListener('input', filterParentDevices);
        parentDeviceSearch.addEventListener('focus', showParentDeviceDropdown);
        parentDeviceSearch.addEventListener('keydown', function(e) {
            const select = document.getElementById('vdev-parent-device');
            if (e.key === 'ArrowDown' && select.style.display === 'block') {
                e.preventDefault();
                select.focus();
            }
        });
    }
    
    const clearParentSearchBtn = document.getElementById('vdev-clear-parent-search');
    if (clearParentSearchBtn) {
        clearParentSearchBtn.addEventListener('click', clearParentDeviceSelection);
    }
    
    // Close parent device dropdown when clicking outside
    document.addEventListener('click', function(e) {
        const parentSelect = document.getElementById('vdev-parent-device');
        const parentSearch = document.getElementById('vdev-parent-device-search');
        const clearBtn = document.getElementById('vdev-clear-parent-search');
        
        if (parentSelect && parentSearch && clearBtn) {
            if (!parentSelect.contains(e.target) && 
                !parentSearch.contains(e.target) && 
                !clearBtn.contains(e.target)) {
                parentSelect.style.display = 'none';
            }
        }
    });
    
    const tagSearch = document.getElementById('vdev-tag-search');
    if (tagSearch) {
        tagSearch.addEventListener('input', filterVirtualDeviceTags);
    }
    
    const selectAllBtn = document.getElementById('vdev-select-all');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', toggleSelectAllTags);
    }
    
    const cancelBtn = document.getElementById('vdev-cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', cancelVirtualDeviceEdit);
    }
    
    // Virtual device search functionality with debouncing
    const vdevSearchInput = document.getElementById('vdev-search-input');
    if (vdevSearchInput) {
        let vdevSearchTimeout;
        vdevSearchInput.addEventListener('input', (e) => {
            clearTimeout(vdevSearchTimeout);
            vdevSearchTimeout = setTimeout(() => {
                loadVirtualDevices(e.target.value.trim());
            }, 300);
        });
    }
});

/**
 * Load all virtual devices
 */
function loadVirtualDevices(searchText = '') {
    const url = searchText ? `/api/virtual-devices?search=${encodeURIComponent(searchText)}` : '/api/virtual-devices';
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            displayVirtualDevicesList(data, searchText);
        })
        .catch(error => {
            console.error('Error loading virtual devices:', error);
            showAlert('danger', 'Failed to load virtual devices');
        });
}

/**
 * Display virtual devices list
 */
function displayVirtualDevicesList(virtualDevices, searchText = '') {
    const container = document.getElementById('virtual-devices-list');
    
    if (!virtualDevices || virtualDevices.length === 0) {
        container.innerHTML = searchText 
            ? '<p class="text-muted text-center py-4">No virtual devices found matching your search</p>'
            : '<p class="text-muted text-center py-4">No virtual devices configured</p>';
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-hover">';
    html += '<thead><tr>';
    html += '<th>Name</th>';
    html += '<th>HWID</th>';
    html += '<th>Parent Device</th>';
    html += '<th>Tag Count</th>';
    html += '<th>Status</th>';
    html += '<th>Actions</th>';
    html += '</tr></thead><tbody>';
    
    virtualDevices.forEach(vdev => {
        const statusClass = vdev.parent_connected && vdev.enabled ? 'success' : 'secondary';
        const statusText = vdev.parent_connected && vdev.enabled ? 'Connected' : 'Stopped';
        
        html += `<tr id="vdev-row-${vdev.id}">`;
        html += `<td><strong>${escapeHtml(vdev.name)}</strong></td>`;
        html += `<td><code>${escapeHtml(vdev.hardware_id)}</code></td>`;
        html += `<td>${escapeHtml(vdev.parent_device_name || 'N/A')}</td>`;
        html += `<td><span class="badge bg-info">${vdev.tag_count}</span></td>`;
        html += `<td><span class="badge bg-${statusClass}">${statusText}</span></td>`;
        html += `<td>`;
        
        if (vdev.enabled) {
            html += `<button class="btn btn-warning btn-sm me-1" onclick="stopVirtualDevice(${vdev.id})" title="Stop">
                        <i class="bi bi-stop-fill"></i>
                     </button>`;
        } else {
            html += `<button class="btn btn-success btn-sm me-1" onclick="startVirtualDevice(${vdev.id})" title="Start">
                        <i class="bi bi-play-fill"></i>
                     </button>`;
        }
        
        html += `<button class="btn btn-primary btn-sm me-1" onclick="editVirtualDevice(${vdev.id})" title="Edit">
                    <i class="bi bi-pencil"></i>
                 </button>`;
        html += `<button class="btn btn-danger btn-sm" onclick="deleteVirtualDevice(${vdev.id}, '${escapeHtml(vdev.name)}')" title="Delete">
                    <i class="bi bi-trash"></i>
                 </button>`;
        
        html += `</td></tr>`;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

/**
 * Load parent device options for dropdown
 */
function loadParentDeviceOptions() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('vdev-parent-device');
            select.innerHTML = '<option value="">Select parent device...</option>';
            
            data.forEach(device => {
                const option = document.createElement('option');
                option.value = device.id;
                option.textContent = `${device.name} (${device.host})`;
                option.dataset.name = device.name;
                option.dataset.host = device.host;
                option.dataset.hwid = device.hardware_id || '';
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading parent devices:', error);
            showAlert('danger', 'Failed to load parent devices');
        });
}

/**
 * Filter parent devices based on search input
 */
function filterParentDevices() {
    const searchTerm = document.getElementById('vdev-parent-device-search').value.toLowerCase();
    const select = document.getElementById('vdev-parent-device');
    const options = select.querySelectorAll('option');
    
    let hasVisibleOptions = false;
    
    options.forEach(option => {
        if (option.value === '') {
            option.style.display = 'none';
            return;
        }
        
        const name = (option.dataset.name || '').toLowerCase();
        const host = (option.dataset.host || '').toLowerCase();
        const hwid = (option.dataset.hwid || '').toLowerCase();
        const optionText = option.textContent.toLowerCase();
        
        const matches = name.includes(searchTerm) || 
                       host.includes(searchTerm) || 
                       hwid.includes(searchTerm) ||
                       optionText.includes(searchTerm);
        
        option.style.display = matches ? 'block' : 'none';
        if (matches) hasVisibleOptions = true;
    });
    
    // Show dropdown if there's search text and visible options
    if (searchTerm && hasVisibleOptions) {
        select.style.display = 'block';
    } else if (!searchTerm) {
        select.style.display = 'none';
    }
}

/**
 * Show parent device dropdown on focus
 */
function showParentDeviceDropdown() {
    const searchInput = document.getElementById('vdev-parent-device-search');
    const select = document.getElementById('vdev-parent-device');
    const valueInput = document.getElementById('vdev-parent-device-value');
    
    // If no device is selected, show all options
    if (!valueInput.value && searchInput.value.trim() === '') {
        const options = select.querySelectorAll('option');
        options.forEach(option => {
            if (option.value !== '') {
                option.style.display = 'block';
            }
        });
        select.style.display = 'block';
    }
}

/**
 * Clear parent device selection
 */
function clearParentDeviceSelection() {
    document.getElementById('vdev-parent-device-search').value = '';
    document.getElementById('vdev-parent-device-value').value = '';
    document.getElementById('vdev-parent-device').value = '';
    document.getElementById('vdev-parent-device').style.display = 'none';
    document.getElementById('vdev-parent-device-selected').style.display = 'none';
    document.getElementById('vdev-tags-container').style.display = 'none';
    selectedTags.clear();
    updateSelectedCount();
}

/**
 * Handle parent device selection change
 */
function handleParentDeviceChange(event) {
    const parentId = event.target.value;
    const tagsContainer = document.getElementById('vdev-tags-container');
    const select = document.getElementById('vdev-parent-device');
    const searchInput = document.getElementById('vdev-parent-device-search');
    const valueInput = document.getElementById('vdev-parent-device-value');
    const selectedDiv = document.getElementById('vdev-parent-device-selected');
    const selectedNameSpan = document.getElementById('vdev-parent-device-name');
    
    if (!parentId) {
        tagsContainer.style.display = 'none';
        return;
    }
    
    // Get selected option text
    const selectedOption = select.options[select.selectedIndex];
    const deviceName = selectedOption.textContent;
    
    // Update UI to show selection
    searchInput.value = '';
    valueInput.value = parentId;
    select.style.display = 'none';
    selectedDiv.style.display = 'block';
    selectedNameSpan.textContent = deviceName;
    
    // Load tags from parent device
    fetch(`/api/virtual-devices/tags/${parentId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                parentDeviceTags = data.tags;
                displayParentTags(data.tags);
                tagsContainer.style.display = 'block';
            } else {
                showAlert('warning', 'No tags found for this device');
            }
        })
        .catch(error => {
            console.error('Error loading parent tags:', error);
            showAlert('danger', 'Failed to load parent device tags');
        });
}

/**
 * Display parent device tags for selection
 */
function displayParentTags(tags) {
    const container = document.getElementById('vdev-tags-list');
    selectedTags.clear();
    
    if (!tags || tags.length === 0) {
        container.innerHTML = '<p class="text-muted small p-2">No tags available</p>';
        updateSelectedCount();
        return;
    }
    
    let html = '';
    tags.forEach(tag => {
        html += `
            <div class="form-check">
                <input class="form-check-input vdev-tag-checkbox" type="checkbox" 
                       value="${tag.id}" id="tag-${tag.id}" 
                       onchange="updateTagSelection(${tag.id})">
                <label class="form-check-label" for="tag-${tag.id}">
                    ${escapeHtml(tag.name)}
                    ${tag.data_type ? `<span class="badge bg-secondary ms-1">${tag.data_type}</span>` : ''}
                </label>
            </div>
        `;
    });
    
    container.innerHTML = html;
    updateSelectedCount();
}

/**
 * Update tag selection
 */
function updateTagSelection(tagId) {
    const checkbox = document.getElementById(`tag-${tagId}`);
    if (checkbox.checked) {
        selectedTags.add(tagId);
    } else {
        selectedTags.delete(tagId);
    }
    updateSelectedCount();
}

/**
 * Update selected tags count
 */
function updateSelectedCount() {
    document.getElementById('vdev-selected-count').textContent = selectedTags.size;
}

/**
 * Toggle select all tags
 */
function toggleSelectAllTags() {
    const checkboxes = document.querySelectorAll('.vdev-tag-checkbox');
    const allSelected = selectedTags.size === parentDeviceTags.length;
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = !allSelected;
        const tagId = parseInt(checkbox.value);
        if (!allSelected) {
            selectedTags.add(tagId);
        } else {
            selectedTags.delete(tagId);
        }
    });
    
    updateSelectedCount();
}

/**
 * Filter tags by search
 */
function filterVirtualDeviceTags() {
    const searchTerm = document.getElementById('vdev-tag-search').value.toLowerCase();
    const checkboxes = document.querySelectorAll('.vdev-tag-checkbox');
    
    checkboxes.forEach(checkbox => {
        const label = checkbox.parentElement;
        const tagName = label.textContent.toLowerCase();
        label.style.display = tagName.includes(searchTerm) ? 'block' : 'none';
    });
}

/**
 * Handle add/edit virtual device form submission
 */
function handleAddVirtualDevice(event) {
    event.preventDefault();
    
    const name = document.getElementById('vdev-name').value;
    const hwid = document.getElementById('vdev-hwid').value;
    const parentDeviceId = document.getElementById('vdev-parent-device-value').value || document.getElementById('vdev-parent-device').value;
    const enabled = document.getElementById('vdev-enabled').checked;
    
    if (!parentDeviceId) {
        showAlert('warning', 'Please select a parent device');
        return;
    }
    
    if (selectedTags.size === 0) {
        showAlert('warning', 'Please select at least one tag');
        return;
    }
    
    const data = {
        name: name,
        hardware_id: hwid,
        parent_device_id: parseInt(parentDeviceId),
        tag_ids: Array.from(selectedTags),
        enabled: enabled
    };
    
    const url = editingVirtualDeviceId 
        ? `/api/virtual-devices/${editingVirtualDeviceId}`
        : '/api/virtual-devices';
    const method = editingVirtualDeviceId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showAlert('success', editingVirtualDeviceId 
                ? 'Virtual device updated successfully' 
                : 'Virtual device created successfully');
            resetVirtualDeviceForm();
            loadVirtualDevices();
        } else {
            showAlert('danger', result.error || 'Failed to save virtual device');
        }
    })
    .catch(error => {
        console.error('Error saving virtual device:', error);
        showAlert('danger', 'Failed to save virtual device');
    });
}

/**
 * Edit virtual device
 */
function editVirtualDevice(vdevId) {
    editingVirtualDeviceId = vdevId;
    
    fetch(`/api/virtual-devices/${vdevId}`)
        .then(response => response.json())
        .then(vdev => {
            // Populate form
            document.getElementById('vdev-name').value = vdev.name;
            document.getElementById('vdev-hwid').value = vdev.hardware_id;
            document.getElementById('vdev-parent-device').value = vdev.parent_device_id;
            document.getElementById('vdev-parent-device-value').value = vdev.parent_device_id;
            document.getElementById('vdev-enabled').checked = vdev.enabled;
            
            // Show selected device
            const select = document.getElementById('vdev-parent-device');
            const selectedOption = select.options[select.selectedIndex];
            if (selectedOption) {
                document.getElementById('vdev-parent-device-selected').style.display = 'block';
                document.getElementById('vdev-parent-device-name').textContent = selectedOption.textContent;
            }
            
            // Load tags and pre-select
            handleParentDeviceChange({target: {value: vdev.parent_device_id}});
            
            // Wait for tags to load, then select them
            setTimeout(() => {
                selectedTags.clear();
                vdev.tags.forEach(tag => {
                    selectedTags.add(tag.tag_id);
                    const checkbox = document.getElementById(`tag-${tag.tag_id}`);
                    if (checkbox) checkbox.checked = true;
                });
                updateSelectedCount();
            }, 500);
            
            // Update button text
            document.getElementById('vdev-submit-btn').innerHTML = '<i class="bi bi-save"></i> Update Virtual Device';
            document.getElementById('vdev-cancel-btn').style.display = 'block';
            
            // Scroll to form
            document.getElementById('add-virtual-device-form').scrollIntoView({behavior: 'smooth'});
        })
        .catch(error => {
            console.error('Error loading virtual device:', error);
            showAlert('danger', 'Failed to load virtual device');
        });
}

/**
 * Delete virtual device
 */
function deleteVirtualDevice(vdevId, vdevName) {
    if (!confirm(`Are you sure you want to delete virtual device "${vdevName}"?`)) {
        return;
    }
    
    fetch(`/api/virtual-devices/${vdevId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showAlert('success', 'Virtual device deleted successfully');
            loadVirtualDevices();
        } else {
            showAlert('danger', result.error || 'Failed to delete virtual device');
        }
    })
    .catch(error => {
        console.error('Error deleting virtual device:', error);
        showAlert('danger', 'Failed to delete virtual device');
    });
}

/**
 * Start virtual device
 */
function startVirtualDevice(vdevId) {
    fetch(`/api/virtual-devices/start/${vdevId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showAlert('success', 'Virtual device started');
            loadVirtualDevices();
        } else {
            showAlert('danger', result.error || 'Failed to start virtual device');
        }
    })
    .catch(error => {
        console.error('Error starting virtual device:', error);
        showAlert('danger', 'Failed to start virtual device');
    });
}

/**
 * Stop virtual device
 */
function stopVirtualDevice(vdevId) {
    fetch(`/api/virtual-devices/stop/${vdevId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showAlert('success', 'Virtual device stopped');
            loadVirtualDevices();
        } else {
            showAlert('danger', result.error || 'Failed to stop virtual device');
        }
    })
    .catch(error => {
        console.error('Error stopping virtual device:', error);
        showAlert('danger', 'Failed to stop virtual device');
    });
}

/**
 * Cancel virtual device edit
 */
function cancelVirtualDeviceEdit() {
    resetVirtualDeviceForm();
}

/**
 * Reset virtual device form
 */
function resetVirtualDeviceForm() {
    editingVirtualDeviceId = null;
    selectedTags.clear();
    
    document.getElementById('add-virtual-device-form').reset();
    document.getElementById('vdev-parent-device-search').value = '';
    document.getElementById('vdev-parent-device-value').value = '';
    document.getElementById('vdev-parent-device').style.display = 'none';
    document.getElementById('vdev-parent-device-selected').style.display = 'none';
    document.getElementById('vdev-tags-container').style.display = 'none';
    document.getElementById('vdev-submit-btn').innerHTML = '<i class="bi bi-plus-lg"></i> Add Virtual Device';
    document.getElementById('vdev-cancel-btn').style.display = 'none';
    
    updateSelectedCount();
}

/**
 * HTML escape utility
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
