# EthernetIP MQTT Bridge with Auto Tag Discovery

A Python-based bridge that reads data from **multiple EthernetIP PLCs simultaneously** and publishes to MQTT brokers. Perfect for industrial IoT applications!

## ✨ Features

- 🔄 **Multi-Device Support** - Connect to unlimited EthernetIP devices
- � **Auto Tag Discovery** - Automatically fetch all available tags from PLC (no manual entry!)
- �📤 Real-time polling and MQTT publishing
- 🌐 Web-based configuration and monitoring dashboard
- 🎮 Individual device control (start/stop/edit/delete)
- 📊 Live status and data visualization per device
- 🧪 Built-in simulator for testing without hardware
- ⚙️ Per-device configuration (tags, polling, topics)

## 🎉 What's New in v2.0

### Auto Tag Discovery (NEW!)
- 🔍 **Automatic Tag Detection** - No need to manually enter tag names!
- ✨ **Test Connection Button** - Preview all available tags before adding device
- 🚀 **Smart Discovery** - System auto-discovers tags if not manually specified
- 📋 **Visual Feedback** - See all discovered tags with badge UI
- ⚡ **Faster Setup** - Connect to devices in seconds

### Multi-Device Management
- ✅ Connect to **multiple PLCs** simultaneously
- ✅ Each device runs independently with its own configuration
- ✅ Add/edit/delete devices through web interface
- ✅ No restart required to change settings
- ✅ Per-device error handling and status monitoring

See **[CHANGELOG.md](CHANGELOG.md)** for full list of changes.

## 🚀 Quick Start

### Option 1: Testing with Simulator (No PLC Required)

1. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Start simulator in one terminal:**
   ```powershell
   python ethernetip_simulator.py
   ```

3. **Start application in another terminal:**
   ```powershell
   python app.py
   ```

4. **Open browser:**
   ```
   http://localhost:5000
   ```

5. **Add your first device:**
   - Fill the "Add New Device" form:
     - **Name**: `Simulator`
     - **Host**: `127.0.0.1`
     - **Slot**: `0` (default)
   - Click "Test Connection & Discover Tags" to see all available tags
   - Click "Add Device" (tags will be auto-discovered)
   - Click "Start" on the device card

6. **Watch it work!** 🎉 Real-time data updates for all discovered tags!

👉 **See [TESTING_MULTI_DEVICE.md](TESTING_MULTI_DEVICE.md) for comprehensive testing guide**

### Option 2: Production with Real PLCs

1. **Install and start application:**
   ```powershell
   pip install -r requirements.txt
   python app.py
   ```

2. **Open web interface:**
   ```
   http://localhost:5000
   ```

3. **Add your PLC devices:**
   - Click "Add New Device" 
   - Enter PLC details (IP, tags, etc.)
   - Start each device

👉 **See [MULTI_DEVICE_GUIDE.md](MULTI_DEVICE_GUIDE.md) for detailed usage instructions**

## 📁 Project Structure

```
├── app.py                      # Main application (multi-device support)
├── app_with_simulator.py       # Legacy single-device with simulator
├── ethernetip_simulator.py     # Mock EthernetIP server for testing
├── requirements.txt            # Python dependencies
├── .env.example               # Configuration template (MQTT settings)
├── MULTI_DEVICE_GUIDE.md      # Complete usage guide (START HERE!)
├── TESTING_MULTI_DEVICE.md    # Testing instructions
├── CHANGELOG.md               # Version history and changes
├── UPGRADE_SUMMARY.md         # Quick reference for v2.0 changes
├── templates/
│   └── index.html             # Multi-device web dashboard
└── static/
    ├── script.js              # Dashboard JavaScript
    └── style.css              # Dashboard styling
```

## 🎯 How It Works

```
┌─────────────┐     EthernetIP     ┌──────────────────┐     MQTT      ┌─────────┐
│   PLC-1     │ ← ← ← ← ← ← ← ← ← │                  │ → → → → → → →│  Broker │
│  (Tags)     │                    │  Multi-Device    │               │  (MQTT) │
└─────────────┘                    │     Bridge       │               └─────────┘
                                   │    (Python)      │
┌─────────────┐                    │                  │
│   PLC-2     │ ← ← ← ← ← ← ← ← ← │  - Device 1      │
│  (Tags)     │                    │  - Device 2      │
└─────────────┘                    │  - Device N      │
                                   └──────────────────┘
┌─────────────┐                           ↓
│   PLC-N     │ ← ← ← ← ← ← ← ← ← ← ┌──────────────┐
│  (Tags)     │                      │ Web Dashboard│
└─────────────┘                      │  (Monitor)   │
                                     └──────────────┘
```

1. **Bridge** connects to multiple EthernetIP devices simultaneously
2. **Each device** polls its configured tags independently
3. **Data** is formatted with device info, timestamps, and value types
4. **MQTT** messages published to device-specific topics like `factory/plc1/Temperature`
5. **Dashboard** provides real-time monitoring and control for all devices

## ⚙️ Configuration

### MQTT Broker (`.env` file)

The MQTT broker is shared across all devices:

```bash
# MQTT Settings (Shared)
MQTT_BROKER=broker.hivemq.com      # MQTT broker address
MQTT_PORT=1883                     # MQTT port
MQTT_CLIENT_ID=ethernetip_bridge   # Client identifier
```

### Devices (Web UI)

Each device is configured independently through the web interface with **automatic tag discovery**:

**Device Settings:**
- **Name**: Friendly identifier (e.g., "PLC-1", "Robot-Arm")
- **Host**: IP address or hostname (e.g., "192.168.1.100")
- **Slot**: EthernetIP slot number (default: 0)
- **Tags**: Auto-discovered from device (or manually specified if needed)
- **MQTT Topic Prefix**: Custom topic path (e.g., "factory/plc1/")
- **Poll Interval**: Seconds between reads (e.g., 5.0)

**Two Ways to Add Devices:**

1. **Preview Tags (Recommended):**
   - Enter device name and host
   - Click "Test Connection & Discover Tags"
   - See all available tags before adding
   - Click "Add Device"

2. **Quick Add:**
   - Enter device name and host
   - Click "Add Device" directly
   - Tags are auto-discovered in background

### Example Multi-Device Setup

```
Device 1: Production Line A
  - Host: 192.168.1.100
  - Tags: Auto-discovered (Speed, Temperature, Status, Counter, etc.)
  - Topic: factory/lineA/
  - Poll: 2.0 seconds

Device 2: Quality Control
  - Host: 192.168.1.101
  - Tags: Auto-discovered (DefectCount, PassRate, InspectionTime, etc.)
  - Topic: factory/qc/
  - Poll: 10.0 seconds

Device 3: Robot Controller
  - Host: 192.168.1.102
  - Tags: Auto-discovered (Position_X, Position_Y, Gripper, Status, etc.)
  - Topic: factory/robot/
  - Poll: 1.0 seconds
```

*Note: With auto-discovery, you don't need to manually specify tag lists anymore!*

## 🧪 Testing Without PLC

The project includes a **simulator mode** so you can test everything on your laptop:

- ✅ No PLC hardware needed
- ✅ Simulated tag values that change realistically
- ✅ Full MQTT publishing
- ✅ Complete web dashboard functionality

**Available Simulated Tags:**
- `Tag1`, `Tag2`, `Tag3` - Generic sensors
- `Temperature`, `Pressure`, `Speed` - Process variables
- `Status`, `Counter` - Status indicators
- `Motor_Running`, `Voltage` - Equipment data

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for complete testing instructions.

---

## 🏭 Production Deployment with Real PLCs

### ⚠️ Important: Switching to Real PLCs

The current configuration uses a **simulator** for testing. To use with **real Allen-Bradley PLCs**, you need to switch the client library.

**Quick Setup for Production:**

1. **Install PyLogix** (recommended for Allen-Bradley):
   ```bash
   pip install pylogix
   ```

2. **Edit `app.py` line 3** - change from:
   ```python
   import ethernetip_simulator as client
   ```
   
   to:
   ```python
   import ethernetip_client_pylogix as client
   ```

3. **That's it!** Tag discovery will now work with your real PLCs.

📖 **See [PRODUCTION_PLC_SETUP.md](PRODUCTION_PLC_SETUP.md) for complete production setup guide**

📋 **See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for quick comparison**

### Why PyLogix?

- ✅ **Native tag enumeration** - works out of the box
- ✅ **Allen-Bradley optimized** - ControlLogix, CompactLogix, Micro800
- ✅ **Simple API** - easy to use
- ✅ **Tag discovery included** - no custom implementation needed

### What About CPPPO?

The standard `cpppo` library does **NOT** include tag enumeration functions. You would need to manually implement CIP Symbol Object queries. Unless you have specific requirements for CPPPO, use PyLogix instead.

---

## 📊 Web Dashboard

The web interface provides comprehensive multi-device management:

### Left Panel: Device Management
- 🟢 **MQTT Connection Status**: Shared broker status
- 📊 **Device Count**: Total configured devices
- ➕ **Add Device Form**: Configure new devices on-the-fly

### Right Panel: Device List
- � **Device Cards**: One card per device showing:
  - Device name and connection status
  - Host address and poll interval
  - Real-time tag values with types
  - Message counters and timestamps
  - Individual controls (Start/Stop/Edit/Delete)
  - Error messages (if any)

### Features
- ⚡ **Real-time Updates**: Auto-refresh every 2 seconds
- 🎮 **Bulk Controls**: Start/Stop all devices at once
- ✏️ **Live Editing**: Modify device settings without restart
- �️ **Dynamic Management**: Add/remove devices anytime
- 📱 **Responsive**: Works on desktop and mobile

## 🔧 Dependencies

- **Flask** - Web server and dashboard
- **cpppo** - EthernetIP/CIP protocol implementation
- **paho-mqtt** - MQTT client library
- **python-dotenv** - Environment variable management

## 📝 Tag Format Examples

### Allen-Bradley ControlLogix/CompactLogix:
```bash
ETHERNETIP_TAGS=Program:MainRoutine.Speed,Program:MainRoutine.Temp
```

### Simple Tags:
```bash
ETHERNETIP_TAGS=Motor1_Speed,Tank_Level,Pressure_PSI
```

### CIP Attribute Format (for simple devices):
```bash
ETHERNETIP_TAGS=@1/1/1,@1/1/7,@4/100/3
```

## 🐛 Troubleshooting

### "No connection could be made" Error
- **For Simulator:** Make sure you're running `app_with_simulator.py`
- **For Real PLC:** 
  - Verify PLC IP address is correct
  - Check network connectivity (`ping <PLC_IP>`)
  - Ensure firewall allows port 44818
  - Confirm PLC supports EthernetIP protocol

### MQTT Not Connecting
- Check internet connection
- Try different MQTT broker: `test.mosquitto.org`
- Verify broker address and port

### Tags Not Reading
- Verify tag names match exactly (case-sensitive)
- Check PLC slot number is correct
- For ControlLogix, include program name: `Program:Main.TagName`

## 📚 Documentation

- **[MULTI_DEVICE_GUIDE.md](MULTI_DEVICE_GUIDE.md)** ⭐ - Complete usage guide for v2.0
- **[TESTING_MULTI_DEVICE.md](TESTING_MULTI_DEVICE.md)** - Testing with multiple devices
- **[UPGRADE_SUMMARY.md](UPGRADE_SUMMARY.md)** - Quick reference for v2.0 changes
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and breaking changes
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Production deployment guide (legacy)
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Single-device testing (legacy)

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📄 License

This project is open source and available for use in commercial and non-commercial applications.

## 💡 Use Cases

- **Multi-Line Manufacturing**: Monitor multiple production lines simultaneously
- **Distributed Systems**: Connect to PLCs across different locations
- **Mixed Environments**: Test and production devices side-by-side
- **Different Poll Rates**: Critical vs. non-critical data collection
- **Vendor Integration**: Multiple PLC brands in one interface
- **Industrial IoT Hub**: Central data collection point
- **Cloud Platform Integration**: Feed data to AWS/Azure/GCP
- **Real-time Dashboards**: Live monitoring and analytics
- **Process Control**: SCADA system integration
- **Predictive Maintenance**: Continuous equipment monitoring

---

**Ready to start?** Follow **[MULTI_DEVICE_GUIDE.md](MULTI_DEVICE_GUIDE.md)** for the complete guide!
