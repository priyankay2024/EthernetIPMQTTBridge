let updateInterval;

function updateStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('bridge-status').textContent = data.running ? 'Running' : 'Stopped';
            document.getElementById('bridge-status').className = data.running ? 'badge bg-success' : 'badge bg-secondary';
            
            document.getElementById('ethernetip-status').textContent = data.ethernetip_connected ? 'Connected' : 'Disconnected';
            document.getElementById('ethernetip-status').className = data.ethernetip_connected ? 'badge bg-success' : 'badge bg-danger';
            
            document.getElementById('mqtt-status').textContent = data.mqtt_connected ? 'Connected' : 'Disconnected';
            document.getElementById('mqtt-status').className = data.mqtt_connected ? 'badge bg-success' : 'badge bg-danger';
            
            document.getElementById('message-count').textContent = data.message_count;
            document.getElementById('last-update').textContent = data.last_update || 'Never';
            
            document.getElementById('ethernetip-host').value = data.ethernetip_host;
            document.getElementById('mqtt-broker').value = data.mqtt_broker;
            document.getElementById('poll-interval').value = data.poll_interval;
            
            const tagsList = document.getElementById('tags-list');
            tagsList.innerHTML = '';
            if (data.tags && data.tags.length > 0) {
                data.tags.forEach(tag => {
                    const badge = document.createElement('span');
                    badge.className = 'badge bg-primary';
                    badge.textContent = tag;
                    tagsList.appendChild(badge);
                });
            } else {
                tagsList.innerHTML = '<span class="text-muted">No tags configured</span>';
            }
            
            const tagValues = document.getElementById('tag-values');
            if (data.last_data && Object.keys(data.last_data).length > 0) {
                tagValues.innerHTML = '';
                for (const [tag, info] of Object.entries(data.last_data)) {
                    if (info.error) {
                        const tagDiv = document.createElement('div');
                        tagDiv.className = 'tag-item border-danger';
                        tagDiv.innerHTML = `
                            <div class="tag-name">${tag}</div>
                            <div class="text-danger">Error: ${info.error}</div>
                        `;
                        tagValues.appendChild(tagDiv);
                    } else {
                        const tagDiv = document.createElement('div');
                        tagDiv.className = 'tag-item';
                        tagDiv.innerHTML = `
                            <div class="tag-name">${tag}</div>
                            <div class="tag-value">${JSON.stringify(info.value)}</div>
                            <div class="tag-type">Type: ${info.type}</div>
                        `;
                        tagValues.appendChild(tagDiv);
                    }
                }
            } else {
                tagValues.innerHTML = '<p class="text-muted">No data available</p>';
            }
            
            if (data.last_error) {
                document.getElementById('error-card').style.display = 'block';
                document.getElementById('error-message').textContent = data.last_error;
            } else {
                document.getElementById('error-card').style.display = 'none';
            }
            
            document.getElementById('start-btn').disabled = data.running;
            document.getElementById('stop-btn').disabled = !data.running;
        })
        .catch(error => {
            console.error('Error fetching status:', error);
        });
}

document.getElementById('start-btn').addEventListener('click', () => {
    fetch('/api/start', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            updateStatus();
        })
        .catch(error => {
            console.error('Error starting bridge:', error);
        });
});

document.getElementById('stop-btn').addEventListener('click', () => {
    fetch('/api/stop', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            updateStatus();
        })
        .catch(error => {
            console.error('Error stopping bridge:', error);
        });
});

updateStatus();
updateInterval = setInterval(updateStatus, 2000);
