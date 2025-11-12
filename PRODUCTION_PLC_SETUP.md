# Production PLC Setup Guide

## Overview
This guide explains how to switch from the simulator to real Allen-Bradley PLCs with automatic tag discovery.

---

## ⚠️ Current Status

**Simulator Mode (Default):**
- ✅ Works out of the box
- ✅ No hardware needed
- ✅ 10 simulated tags
- ❌ Not for production use

**Production Mode (Real PLCs):**
- Requires configuration changes
- Needs real PLC hardware
- Supports tag auto-discovery
- Production-ready

---

## 🔄 Two Options for Real PLC Support

### Option 1: PyLogix (RECOMMENDED ⭐)

**Best for Allen-Bradley PLCs**

**Pros:**
- ✅ Excellent tag enumeration support
- ✅ Simple API
- ✅ Works with ControlLogix, CompactLogix, Micro800
- ✅ Active development and support
- ✅ Better error messages

**Cons:**
- ❌ Allen-Bradley only (no other vendors)

---

### Option 2: CPPPO

**Best for cross-vendor compatibility**

**Pros:**
- ✅ Full CIP protocol implementation
- ✅ Supports multiple vendors (theoretically)
- ✅ Lower-level control

**Cons:**
- ❌ Tag enumeration is complex
- ❌ Less documentation
- ❌ May require custom CIP commands

---

## 🚀 Setup Instructions

### Method A: Using PyLogix (Recommended)

#### Step 1: Install PyLogix

```powershell
pip install pylogix
```

#### Step 2: Update app.py

Change line 3 in `app.py`:

**FROM:**
```python
import ethernetip_simulator as client
```

**TO:**
```python
import ethernetip_client_pylogix as client
```

#### Step 3: Test Connection

```powershell
# Edit ethernetip_client_pylogix.py and set your PLC IP
# Change line: PLC_HOST = "192.168.1.100"

python ethernetip_client_pylogix.py
```

You should see output like:
```
✓ SUCCESS! Discovered 47 tags:
  1. Temperature
  2. Pressure
  3. Speed
  ...
```

#### Step 4: Start Application

```powershell
python app.py
```

#### Step 5: Add Your PLC

1. Open http://localhost:5000
2. Click "Add New Device"
3. Enter PLC IP address
4. Click "Test Connection & Discover Tags"
5. See all your PLC tags!
6. Click "Add Device"

**Done! 🎉**

---

### Method B: Using CPPPO (Advanced)

#### Step 1: Already Installed

CPPPO is already in `requirements.txt`:
```powershell
pip install cpppo
```

#### Step 2: Update app.py

**FROM:**
```python
import ethernetip_simulator as client
```

**TO:**
```python
import ethernetip_client_real as client
```

#### Step 3: ⚠️ Implement Tag Enumeration

**PROBLEM:** CPPPO doesn't have built-in tag enumeration!

You need to implement CIP Symbol Object queries. See `ethernetip_client_real.py` for a starting implementation, but **this is complex and may not work on all PLCs**.

**Recommendation:** Use PyLogix instead (Method A).

---

## 📋 Comparison Table

| Feature | Simulator | PyLogix | CPPPO |
|---------|-----------|---------|-------|
| Tag Discovery | ✅ Built-in | ✅ Native Support | ⚠️ Manual Implementation |
| Allen-Bradley | ✅ Mock | ✅ Excellent | ⚠️ Basic |
| Other Vendors | N/A | ❌ No | ⚠️ Maybe |
| Ease of Use | ✅ Easy | ✅ Easy | ❌ Complex |
| Production Ready | ❌ No | ✅ Yes | ⚠️ With Work |
| Documentation | ✅ Good | ✅ Good | ⚠️ Limited |
| **Recommendation** | **Testing** | **✨ Production** | **Advanced Only** |

---

## 🔧 Code Changes Required

### File: `app.py`

**Line 3 - Choose your client:**

```python
# OPTION 1: Simulator (testing)
import ethernetip_simulator as client

# OPTION 2: PyLogix (recommended for production)
# import ethernetip_client_pylogix as client

# OPTION 3: CPPPO (advanced, requires implementation)
# import ethernetip_client_real as client
```

**That's the only change needed!** ✨

All three implementations provide:
- `list_all_tags(host, slot, timeout)`
- `connector(host, timeout)`
- `parse_operations(tags)`

---

## 🧪 Testing with Real PLC

### Pre-flight Checklist

Before testing, verify:

- [ ] PLC is powered on and online
- [ ] PLC has EtherNet/IP enabled
- [ ] Your computer can ping the PLC IP
- [ ] Firewall allows port 44818 (EtherNet/IP)
- [ ] You know the PLC slot number (usually 0)
- [ ] PLC has some tags configured

### Test Script

```powershell
# For PyLogix
python ethernetip_client_pylogix.py

# For CPPPO
python ethernetip_client_real.py
```

### Expected Output (Success)

```
======================================================================
PyLogix Tag Discovery Test
======================================================================

Target PLC: 192.168.1.100
Slot: 0

Attempting to discover tags...
----------------------------------------------------------------------

[TAG DISCOVERY] Connecting to PLC at 192.168.1.100 using pylogix...
[TAG DISCOVERY]   Found: Temperature (Type: REAL)
[TAG DISCOVERY]   Found: Pressure (Type: REAL)
[TAG DISCOVERY]   Found: Speed (Type: DINT)
...
[TAG DISCOVERY] Successfully discovered 47 tags

----------------------------------------------------------------------
✓ SUCCESS! Discovered 47 tags:
----------------------------------------------------------------------
  1. ConveyorSpeed
  2. MotorStatus
  3. Pressure
  ...
```

### Common Errors

#### Error: "Connection timeout"
```
Troubleshooting:
  1. Verify PLC IP: ping 192.168.1.100
  2. Check network connectivity
  3. Verify firewall settings
  4. Ensure PLC is online
```

**Solutions:**
- Verify PLC IP address
- Check physical network connection
- Disable firewall temporarily to test
- Try from another computer on same network

#### Error: "No tags found"
```
⚠ No tags discovered automatically.
```

**Possible Causes:**
- PLC doesn't support tag enumeration
- Wrong slot number
- Security/permissions on PLC
- PLC firmware too old

**Solutions:**
- Try different slot numbers (0, 1, 2)
- Check PLC security settings
- Update PLC firmware
- Manually specify tags (fallback option)

---

## 🔌 Supported PLC Models

### With PyLogix:

**✅ Fully Supported:**
- Allen-Bradley ControlLogix (5000 series)
- Allen-Bradley CompactLogix (5000 series)
- Allen-Bradley Micro800 series
- Allen-Bradley MicroLogix (some models)

**❌ Not Supported:**
- Siemens PLCs
- Modicon PLCs
- Omron PLCs
- Other manufacturers

### With CPPPO:

**⚠️ Theoretical Support** (requires implementation):
- Any CIP-compatible device
- May work with non-AB PLCs
- Requires custom CIP commands

---

## 🛠️ Manual Tag Specification (Fallback)

If auto-discovery doesn't work, you can still manually specify tags:

### In the Web UI:

When adding a device, you can provide tags manually in the API call or by modifying the JavaScript to re-enable manual entry.

### API Call Example:

```javascript
fetch('/api/devices', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        name: "PLC-1",
        host: "192.168.1.100",
        slot: 0,
        tags: ["Temperature", "Pressure", "Speed"],  // Manual tags
        mqtt_topic_prefix: "factory/plc1/",
        poll_interval: 5.0
    })
})
```

If you provide tags, auto-discovery is skipped.

---

## 🚨 Important Notes

### Security

- **Firewall:** Port 44818 (TCP/UDP) must be open
- **PLC Access:** Ensure your IP has read permissions
- **Network Segmentation:** Consider VLAN for industrial devices

### Performance

- **Poll Interval:** Don't poll too frequently (< 1 second)
- **Tag Count:** Large tag lists (100+) may slow discovery
- **Network Load:** Consider network bandwidth

### Best Practices

1. **Test First:** Always test with simulator before production
2. **Start Small:** Add one device, verify, then add more
3. **Monitor Logs:** Watch console output for errors
4. **Document Tags:** Keep a list of important tags
5. **Backup Config:** Save working configurations

---

## 📚 Additional Resources

### PyLogix Documentation:
- GitHub: https://github.com/dmroeder/pylogix
- Examples: https://github.com/dmroeder/pylogix/tree/master/examples

### CPPPO Documentation:
- GitHub: https://github.com/pjkundert/cpppo
- Wiki: https://github.com/pjkundert/cpppo/wiki

### Allen-Bradley Resources:
- EtherNet/IP Developer Guide
- ControlLogix System User Manual
- Rockwell Automation Knowledge Base

---

## 🆘 Getting Help

### Simulator Works But Real PLC Doesn't?

1. **Check the test script output**
   ```powershell
   python ethernetip_client_pylogix.py
   ```

2. **Verify network connectivity**
   ```powershell
   ping 192.168.1.100
   ```

3. **Check PLC configuration**
   - Is EtherNet/IP enabled?
   - Are tags configured?
   - Is the PLC online?

4. **Review logs**
   - Look for connection errors
   - Check tag discovery messages
   - Verify API responses

### Still Having Issues?

- Review `AUTO_TAG_DISCOVERY_GUIDE.md` for troubleshooting
- Check `CHANGES.md` for implementation details
- See example configurations in documentation

---

## ✅ Production Deployment Checklist

Before going live:

- [ ] PyLogix installed and tested
- [ ] Test script confirms tag discovery works
- [ ] app.py updated to use production client
- [ ] PLC IP addresses documented
- [ ] MQTT broker configured
- [ ] Firewall rules configured
- [ ] Network connectivity verified
- [ ] Tags discovered and validated
- [ ] Poll intervals optimized
- [ ] Error handling tested
- [ ] Monitoring in place

---

## Summary

**For Allen-Bradley PLCs:**
1. Install PyLogix: `pip install pylogix`
2. Change line 3 in `app.py` to: `import ethernetip_client_pylogix as client`
3. Test: `python ethernetip_client_pylogix.py`
4. Start: `python app.py`
5. Done! 🎉

**Everything else stays the same** - the web UI, MQTT publishing, and all other features work identically.

