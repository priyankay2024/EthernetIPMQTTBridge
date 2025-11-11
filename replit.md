# EthernetIP to MQTT Bridge

## Overview
A Python Flask application that bridges EthernetIP devices (PLCs) to MQTT brokers. The application continuously reads data from EthernetIP devices and publishes it to configurable MQTT topics, with a web interface for monitoring and configuration.

## Recent Changes
- Initial project setup (November 11, 2025)
- Implemented core EthernetIP to MQTT bridging functionality
- Created Flask web interface for monitoring
- Added configuration system with environment variables
- Implemented MQTT reconnection logic with exponential backoff (5s to 60s)
- Secured configuration - uses environment variables only (no file writing)
- **Switched from pycomm3 to cpppo library** for better EthernetIP compatibility (November 11, 2025)

## Project Architecture
- **Backend**: Flask application with threading for continuous data polling
- **EthernetIP**: Uses cpppo library for PLC communication (supports ControlLogix, CompactLogix, MicroLogix, PowerFlex)
- **MQTT**: Uses paho-mqtt client for message publishing
- **Frontend**: Bootstrap 5 with vanilla JavaScript for status updates

## Key Features
- Real-time data reading from EthernetIP devices
- Automatic MQTT publishing with configurable topics
- Web-based monitoring dashboard with live status updates
- Configuration management via environment variables
- Connection status monitoring for both EthernetIP and MQTT
- MQTT auto-reconnection with exponential backoff
- Error handling and comprehensive logging
- Secure configuration (read-only, no credential writing)

## Configuration
Set the following environment variables in Replit Secrets or create a `.env` file:
- `ETHERNETIP_HOST` - IP address of your PLC (default: 192.168.1.10)
- `ETHERNETIP_SLOT` - PLC slot number (default: 0)
- `ETHERNETIP_TAGS` - Comma-separated list of tags to read (e.g., "Tag1,Tag2,Tag3")
- `MQTT_BROKER` - MQTT broker hostname (default: broker.hivemq.com)
- `MQTT_PORT` - MQTT broker port (default: 1883)
- `MQTT_TOPIC_PREFIX` - Prefix for MQTT topics (default: ethernetip/)
- `MQTT_CLIENT_ID` - MQTT client identifier (default: ethernetip_bridge)
- `POLL_INTERVAL` - Seconds between reads (default: 1.0)

See `.env.example` for reference.

## Dependencies
- Flask: Web framework
- cpppo: EthernetIP/CIP communication (v5.2.5)
- paho-mqtt: MQTT client
- python-dotenv: Environment configuration

## EthernetIP Tag Formats
cpppo supports various tag formats:
- Simple tags: `"TagName"`, `"Motor_Speed"`
- Array elements: `"Tag[5]"` (single element)
- Array ranges: `"Tag[0-10]"` (range of elements)
- CIP attributes: `"@Class/Instance/Attribute"` (e.g., `"@1/1/7"`)

## Troubleshooting
- Ensure your PLC is accessible on the network
- Verify the correct IP address and slot number
- Check that tag names match exactly (case-sensitive)
- For simple devices (MicroLogix, PowerFlex), you may need to use CIP attribute format
