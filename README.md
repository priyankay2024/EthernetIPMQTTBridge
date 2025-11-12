# EthernetIP to MQTT Bridge 🔌 → 📡

A Python-based bridge that reads data from EthernetIP PLCs and publishes it to MQTT brokers. Perfect for industrial IoT applications!

## ✨ Features

- 🔄 Real-time polling of EthernetIP tags
- 📤 Automatic publishing to MQTT topics
- 🌐 Web-based monitoring dashboard
- 🎮 Easy start/stop controls
- 📊 Live status and data visualization
- 🧪 Built-in simulator for testing without hardware

## 🚀 Quick Start

### For Testing (No PLC Required)

1. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Copy environment config:**
   ```powershell
   Copy-Item .env.example .env
   ```

3. **Run with simulator:**
   ```powershell
   python app_with_simulator.py
   ```

4. **Open browser:**
   ```
   http://localhost:5000
   ```

5. **Click "Start Bridge"** and watch it work! 🎉

👉 **See [TESTING_GUIDE.md](TESTING_GUIDE.md) for detailed testing instructions**

### For Production (Real PLC)

1. **Update `.env` with your PLC details:**
   ```bash
   ETHERNETIP_HOST=192.168.1.100  # Your PLC IP
   ETHERNETIP_TAGS=Tag1,Tag2,Tag3  # Your tag names
   ```

2. **Run the application:**
   ```powershell
   python app.py
   ```

👉 **See [SETUP_GUIDE.md](SETUP_GUIDE.md) for production deployment**

## 📁 Project Structure

```
├── app.py                      # Main application (connects to real PLC)
├── app_with_simulator.py       # Testing version (uses simulator)
├── ethernetip_simulator.py     # Mock EthernetIP client
├── requirements.txt            # Python dependencies
├── .env.example               # Configuration template
├── TESTING_GUIDE.md           # Testing instructions
├── SETUP_GUIDE.md             # Production setup guide
├── templates/
│   └── index.html             # Web dashboard
└── static/
    ├── script.js              # Dashboard JavaScript
    └── style.css              # Dashboard styling
```

## 🎯 How It Works

```
┌─────────────┐     EthernetIP     ┌──────────────┐     MQTT      ┌─────────┐
│     PLC     │ ← ← ← ← ← ← ← ← ← │    Bridge    │ → → → → → → →│  Broker │
│  (Tags)     │   Read Tags        │   (Python)   │   Publish     │  (MQTT) │
└─────────────┘                    └──────────────┘               └─────────┘
                                           ↓
                                    ┌──────────────┐
                                    │ Web Dashboard│
                                    │  (Monitor)   │
                                    └──────────────┘
```

1. **Bridge** connects to EthernetIP PLC and reads configured tags
2. **Data** is formatted with timestamps and value types
3. **MQTT** messages are published to topics like `ethernetip/Tag1`
4. **Dashboard** provides real-time monitoring and control

## ⚙️ Configuration

Edit `.env` file to configure:

```bash
# EthernetIP Settings
ETHERNETIP_HOST=127.0.0.1          # PLC IP address
ETHERNETIP_SLOT=0                  # PLC slot number
ETHERNETIP_TAGS=Tag1,Tag2,Tag3     # Comma-separated tags

# MQTT Settings
MQTT_BROKER=broker.hivemq.com      # MQTT broker address
MQTT_PORT=1883                     # MQTT port
MQTT_TOPIC_PREFIX=ethernetip/      # Topic prefix
MQTT_CLIENT_ID=ethernetip_bridge   # Client identifier

# Polling Settings
POLL_INTERVAL=1.0                  # Seconds between reads
```

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

## 📊 Web Dashboard

The web interface shows:

- 🟢 **Connection Status**: Bridge, EthernetIP, and MQTT status
- 📈 **Live Data**: Current values of all configured tags
- 🎮 **Controls**: Start/Stop bridge operation
- ⚙️ **Configuration**: View current settings
- 🔴 **Error Display**: Clear error messages when issues occur

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

- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Complete testing instructions with simulator
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Production deployment guide
- **[replit.md](replit.md)** - Original Replit deployment notes

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📄 License

This project is open source and available for use in commercial and non-commercial applications.

## 💡 Use Cases

- Industrial IoT data collection
- PLC data logging and monitoring
- Integration with cloud platforms
- Real-time dashboards and analytics
- SCADA system integration
- Process monitoring and alerting

---

**Ready to start?** Follow the [TESTING_GUIDE.md](TESTING_GUIDE.md) to test with the simulator!
