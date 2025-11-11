# EthernetIP to MQTT Bridge - Setup Guide

## Quick Start

Your bridge application is running, but you need to configure it to connect to your PLC. Here's how:

## Step 1: Configure Environment Variables

You need to set the following environment variables in **Replit Secrets**:

### Required Configuration:

1. **Click on "Tools" → "Secrets"** in the left sidebar of Replit

2. **Add these secrets:**

   | Secret Name | Example Value | Description |
   |------------|---------------|-------------|
   | `ETHERNETIP_HOST` | `192.168.1.100` | IP address of your PLC |
   | `ETHERNETIP_TAGS` | `Tag1,Tag2,Tag3` | Comma-separated list of tags to read |

### Optional Configuration:

   | Secret Name | Default Value | Description |
   |------------|---------------|-------------|
   | `ETHERNETIP_SLOT` | `0` | PLC slot number |
   | `MQTT_BROKER` | `broker.hivemq.com` | MQTT broker hostname |
   | `MQTT_PORT` | `1883` | MQTT broker port |
   | `MQTT_TOPIC_PREFIX` | `ethernetip/` | Prefix for MQTT topics |
   | `MQTT_CLIENT_ID` | `ethernetip_bridge` | MQTT client identifier |
   | `POLL_INTERVAL` | `1.0` | Seconds between reads |

## Step 2: Tag Format Examples

The `cpppo` library supports various tag formats:

### For Allen-Bradley PLCs (ControlLogix, CompactLogix):
```
ETHERNETIP_TAGS=Program:MainRoutine.Speed,Program:MainRoutine.Temperature,Motor_Running
```

### For Array Tags:
```
ETHERNETIP_TAGS=Tag[5],Tag[0-10]
```

### For Simple Devices (MicroLogix, PowerFlex) using CIP attributes:
```
ETHERNETIP_TAGS=@1/1/1,@1/1/7,@4/100/3
```

CIP format: `@Class/Instance/Attribute`

## Step 3: Restart and Test

After adding your secrets:

1. **Restart the application** - The workflow will automatically restart and pick up your new configuration
2. **Open the web interface** - Click the "Webview" tab
3. **Click "Start Bridge"**
4. **Check the status**:
   - Both **EthernetIP** and **MQTT** should show "Connected" (green)
   - You should see tag values in the "Latest Tag Values" section
   - Messages will be published to MQTT topics like: `ethernetip/Tag1`, `ethernetip/Tag2`, etc.

## Troubleshooting

### EthernetIP shows "Disconnected":
- ✅ Verify your PLC IP address is correct and reachable from this network
- ✅ Check that tag names match exactly (case-sensitive)
- ✅ Ensure your firewall allows connections on port 44818 (EthernetIP default)
- ✅ For simple devices, try CIP attribute format instead: `@1/1/1`

### MQTT shows "Disconnected":
- ✅ Check your MQTT broker is accessible
- ✅ Verify the broker hostname and port
- ✅ Check if authentication is required (not currently supported)

### Error: "No tags configured":
- ✅ Make sure you've set the `ETHERNETIP_TAGS` secret
- ✅ Tags should be comma-separated with no spaces

## Example Configuration

Here's a complete example for a ControlLogix PLC:

```
ETHERNETIP_HOST=192.168.1.50
ETHERNETIP_SLOT=0
ETHERNETIP_TAGS=Program:MainRoutine.Speed,Program:MainRoutine.Pressure,Program:MainRoutine.Status
MQTT_BROKER=mqtt.mycompany.com
MQTT_PORT=1883
MQTT_TOPIC_PREFIX=plc/line1/
POLL_INTERVAL=2.0
```

This will:
- Read 3 tags from PLC at 192.168.1.50 every 2 seconds
- Publish to topics:
  - `plc/line1/Program:MainRoutine.Speed`
  - `plc/line1/Program:MainRoutine.Pressure`
  - `plc/line1/Program:MainRoutine.Status`

## Need Help?

Check the application logs for detailed error messages:
- Click "Tools" → "Console" to see real-time connection attempts and errors
- Look for messages like "Connecting to EthernetIP device at..." to see what's happening
