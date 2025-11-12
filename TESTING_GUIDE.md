# 🚀 Quick Start Guide - Testing with Simulator

This guide will help you test the EthernetIP to MQTT Bridge on your local laptop **without** requiring real PLC hardware.

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## 🛠️ Setup Steps

### 1. Install Dependencies

Open PowerShell in the project directory and run:

```powershell
pip install -r requirements.txt
```

This will install:
- Flask (web server)
- cpppo (EthernetIP protocol library)
- paho-mqtt (MQTT client)
- python-dotenv (environment variables)

### 2. Create Environment Configuration

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

The default configuration is already set for simulator mode:
- `ETHERNETIP_HOST=127.0.0.1` (localhost)
- `ETHERNETIP_TAGS=Tag1,Tag2,Tag3,Temperature,Pressure,Speed,Status`
- `MQTT_BROKER=broker.hivemq.com` (public test broker)

You can edit `.env` file to customize these settings.

### 3. Run the Application with Simulator

Run the simulator version of the application:

```powershell
python app_with_simulator.py
```

You should see output like:
```
======================================================================
          EthernetIP to MQTT Bridge - SIMULATOR MODE
======================================================================

Starting Flask application on http://0.0.0.0:5000
Open your browser and navigate to the URL above

This version uses a MOCK EthernetIP client for testing.
No real PLC hardware is required!
======================================================================
```

### 4. Open the Web Interface

Open your browser and go to:
```
http://localhost:5000
```

### 5. Start the Bridge

1. Click the **"Start Bridge"** button in the web interface
2. Watch the status indicators turn green:
   - ✅ Bridge Status: Running
   - ✅ EthernetIP: Connected (to simulator)
   - ✅ MQTT: Connected

3. You'll see live tag values updating in the "Latest Tag Values" section

## 📊 What You Should See

The simulator provides the following simulated tags with dynamic values:

| Tag Name | Description | Value Range |
|----------|-------------|-------------|
| `Tag1` | Generic sensor 1 | ~100 ± 5 |
| `Tag2` | Generic sensor 2 | ~25 ± 2 |
| `Tag3` | Generic sensor 3 | 40-45 |
| `Temperature` | Temperature reading | ~72°F ± 1 |
| `Pressure` | Pressure reading | ~14.7 psi ± 0.5 |
| `Speed` | Motor speed | 1400-1600 RPM |
| `Status` | On/off status | 0 or 1 |
| `Counter` | Incrementing counter | 0-9999 |

The values update every second to simulate a live PLC.

## 🔍 Viewing MQTT Messages

To verify that data is being published to MQTT, you can use an MQTT client:

### Option 1: Use MQTT Explorer (Recommended)
1. Download [MQTT Explorer](http://mqtt-explorer.com/)
2. Connect to `broker.hivemq.com` on port `1883`
3. Look for topics under `ethernetip/test/`
4. You should see messages like:
   ```json
   {
     "value": 100.5,
     "type": "float",
     "timestamp": "2025-11-11T12:34:56.789"
   }
   ```

### Option 2: Use Command Line (mosquitto_sub)
```powershell
mosquitto_sub -h broker.hivemq.com -t "ethernetip/test/#" -v
```

## 🎯 Understanding the Simulator

The simulator (`ethernetip_simulator.py`) provides a **mock EthernetIP client** that:
- ✅ Simulates successful connections without needing a real PLC
- ✅ Generates realistic, dynamic tag values that change over time
- ✅ Returns data in the same format as real cpppo EthernetIP client
- ✅ Works entirely on your local machine (no network required)

## 🔄 Switching to Real PLC

When you're ready to connect to a real PLC:

1. **Use the original app.py:**
   ```powershell
   python app.py
   ```

2. **Update your .env file:**
   ```bash
   ETHERNETIP_HOST=192.168.1.100  # Your PLC's IP address
   ETHERNETIP_TAGS=Program:MainRoutine.Speed,Program:MainRoutine.Temp
   ```

3. **Ensure network connectivity:**
   - Your laptop must be on the same network as the PLC
   - Firewall must allow port 44818 (EthernetIP/CIP)
   - PLC must support EthernetIP protocol

## ❓ Troubleshooting

### Error: "Module not found"
```powershell
pip install -r requirements.txt
```

### Port 5000 already in use
Change the port in `app_with_simulator.py`:
```python
app.run(host='0.0.0.0', port=5001, debug=False)
```

### MQTT not connecting
- Check your internet connection (broker.hivemq.com is online)
- Try a different public broker in `.env`:
  ```
  MQTT_BROKER=test.mosquitto.org
  ```

### Web interface not loading
- Make sure Python script is running
- Check firewall settings
- Try accessing `http://127.0.0.1:5000` instead

## 📝 Testing Different Scenarios

### Add More Tags
Edit `.env` and add more tags:
```bash
ETHERNETIP_TAGS=Tag1,Tag2,Tag3,Temperature,Pressure,Speed,Status,Counter,Motor_Running,Voltage
```

All these tags are available in the simulator.

### Change Polling Speed
Update the poll interval (in seconds):
```bash
POLL_INTERVAL=0.5  # Poll twice per second
```

### Use Private MQTT Broker
```bash
MQTT_BROKER=your-broker.com
MQTT_PORT=1883
MQTT_TOPIC_PREFIX=factory/plc1/
```

## 🎉 Success!

You now have a fully functional EthernetIP to MQTT bridge running in simulator mode! You can:
- ✅ Test the entire workflow without PLC hardware
- ✅ Develop and debug your application
- ✅ Verify MQTT publishing works correctly
- ✅ Understand how the system works before deploying to production

## 📚 Additional Files

- `app.py` - Original version (connects to real PLC)
- `app_with_simulator.py` - Simulator version (for testing)
- `ethernetip_simulator.py` - Mock EthernetIP client
- `.env` - Your configuration (not committed to git)
- `.env.example` - Example configuration template

---

**Need Help?** Check the console output for detailed logs showing connection attempts and data reads.
