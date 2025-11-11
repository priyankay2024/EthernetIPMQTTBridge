# EthernetIP to MQTT Bridge

## Overview
A Python Flask application that bridges EthernetIP devices (PLCs) to MQTT brokers. The application continuously reads data from EthernetIP devices and publishes it to configurable MQTT topics, with a web interface for monitoring and configuration.

## Recent Changes
- Initial project setup (November 11, 2025)
- Implemented core EthernetIP to MQTT bridging functionality
- Created Flask web interface for monitoring
- Added configuration system with environment variables

## Project Architecture
- **Backend**: Flask application with threading for continuous data polling
- **EthernetIP**: Uses pycomm3 library for PLC communication
- **MQTT**: Uses paho-mqtt client for message publishing
- **Frontend**: Bootstrap 5 with vanilla JavaScript for status updates

## Key Features
- Real-time data reading from EthernetIP devices
- Automatic MQTT publishing with configurable topics
- Web-based monitoring dashboard
- Configuration management via environment variables
- Connection status monitoring
- Error handling and retry logic

## Configuration
Copy `.env.example` to `.env` and configure:
- EthernetIP device settings (host, slot, tags)
- MQTT broker connection details
- Polling interval

## Dependencies
- Flask: Web framework
- pycomm3: EthernetIP/CIP communication
- paho-mqtt: MQTT client
- python-dotenv: Environment configuration
