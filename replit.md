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

## Project Architecture
- **Backend**: Flask application with threading for continuous data polling
- **EthernetIP**: Uses pycomm3 library for PLC communication
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
- pycomm3: EthernetIP/CIP communication
- paho-mqtt: MQTT client
- python-dotenv: Environment configuration
