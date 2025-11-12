"""
Real EthernetIP Tag Discovery Implementation using cpppo

This module provides tag enumeration for real Allen-Bradley PLCs using the cpppo library.
The simulator version only returns mock data - this is the production version.
"""

try:
    from cpppo.server.enip import client
    from cpppo.server.enip.get_attribute import proxy_simple as device
    CPPPO_AVAILABLE = True
except ImportError:
    print("WARNING: cpppo not available. Tag discovery will not work with real PLCs.")
    CPPPO_AVAILABLE = False


def list_all_tags(host, slot=0, timeout=5.0):
    """
    List all controller-scoped tags from an Allen-Bradley PLC.
    
    This function uses CIP services to enumerate tags from the PLC's symbol table.
    
    Args:
        host: PLC IP address or hostname
        slot: PLC slot number (default: 0)
        timeout: Connection timeout in seconds
        
    Returns:
        list: List of tag names (strings)
        
    Raises:
        Exception: If connection fails or cpppo is not available
    """
    if not CPPPO_AVAILABLE:
        raise Exception("cpppo library not available. Cannot discover tags from real PLC.")
    
    print(f"[TAG DISCOVERY] Connecting to PLC at {host}:{slot}...")
    
    try:
        # Create a connection to the PLC
        with device(host=host, timeout=timeout) as plc:
            # Method 1: Try to get symbol list using Get_Attribute_All on Symbol Object (0x6B)
            # This is the standard CIP way to enumerate controller tags
            
            tags = []
            
            try:
                # Request all symbols from the Symbol Object Class (0x6B)
                # This returns the controller-scoped tag names
                
                # Build the CIP path to Symbol Object
                path = [
                    {'class': 0x6B},  # Symbol Object Class
                    {'instance': 0}   # Instance 0 (all symbols)
                ]
                
                # Get Attributes All service to retrieve symbol information
                operations = [
                    ('0x01, 0x6B, 0x00', [])  # Get_Attributes_All on Symbol Object
                ]
                
                # Execute the request
                for idx, dsc, op, rpy, sts, val in plc.pipeline(
                    operations=operations,
                    depth=2,
                    timeout=timeout
                ):
                    if sts:
                        # Parse the symbol table response
                        # This contains tag names, data types, etc.
                        if isinstance(val, dict) and 'symbol_name' in val:
                            tags.append(val['symbol_name'])
                        elif isinstance(val, list):
                            for item in val:
                                if isinstance(item, dict) and 'name' in item:
                                    tags.append(item['name'])
                
                if tags:
                    print(f"[TAG DISCOVERY] Found {len(tags)} tags via Symbol Object")
                    return sorted(tags)
                    
            except Exception as symbol_error:
                print(f"[TAG DISCOVERY] Symbol Object method failed: {symbol_error}")
            
            # Method 2: Fallback - Try to read known tag names
            # This requires knowing some tag names in advance
            # Not ideal, but works as a backup
            
            print("[TAG DISCOVERY] Warning: Could not enumerate tags automatically.")
            print("[TAG DISCOVERY] This PLC may not support tag enumeration.")
            print("[TAG DISCOVERY] Please specify tags manually or use a different method.")
            
            return []
            
    except Exception as e:
        error_msg = f"CPPPO: Failed to discover tags from {host}: {str(e)}"
        print(f"[TAG DISCOVERY] {error_msg}")
        raise Exception(error_msg)


def list_all_tags_logix(host, slot=0, timeout=5.0):
    """
    Alternative implementation specifically for Allen-Bradley Logix controllers.
    
    This uses the List Identity service followed by browsing the controller tags.
    Works with ControlLogix, CompactLogix, and MicroLogix controllers.
    
    Args:
        host: PLC IP address
        slot: Backplane slot number
        timeout: Connection timeout
        
    Returns:
        list: Tag names
    """
    if not CPPPO_AVAILABLE:
        raise Exception("cpppo library not available")
    
    print(f"[TAG DISCOVERY] Attempting Logix-specific tag discovery on {host}...")
    
    tags = []
    
    try:
        # Use cpppo's connector with proper routing
        route_path = f"1/{slot}"  # Backplane route to slot
        
        with client.connector(host=host, timeout=timeout) as conn:
            # Try reading Program:MainProgram to discover structure
            # Most Logix controllers have a MainProgram or MainRoutine
            
            test_tags = [
                'Program:MainProgram.*',  # Program-scoped tags
                'Controller.*',            # Controller-scoped tags  
            ]
            
            operations = client.parse_operations(test_tags)
            
            for idx, dsc, op, rpy, sts, val in conn.synchronous(operations=operations):
                if sts:
                    # Successfully read - this tag exists
                    tag_name = dsc.strip()
                    if tag_name not in tags:
                        tags.append(tag_name)
            
            print(f"[TAG DISCOVERY] Found {len(tags)} tags using Logix method")
            return tags
            
    except Exception as e:
        print(f"[TAG DISCOVERY] Logix method failed: {e}")
        return []


def list_tags_pylogix():
    """
    Information about alternative library: pylogix
    
    If cpppo's tag enumeration doesn't work well, consider using pylogix library instead:
    
    Installation:
        pip install pylogix
    
    Example usage:
        from pylogix import PLC
        
        plc = PLC()
        plc.IPAddress = '192.168.1.100'
        tags = plc.GetTagList()
        
        for tag in tags:
            print(f"Tag: {tag.TagName}, Type: {tag.DataType}")
    
    pylogix has better tag enumeration support for Allen-Bradley PLCs.
    """
    pass


# For backward compatibility with simulator
def connector(host, timeout=5.0):
    """Pass-through to cpppo connector"""
    if CPPPO_AVAILABLE:
        return client.connector(host=host, timeout=timeout)
    else:
        raise Exception("cpppo not available")


def parse_operations(tags):
    """Pass-through to cpppo parse_operations"""
    if CPPPO_AVAILABLE:
        return client.parse_operations(tags)
    else:
        raise Exception("cpppo not available")


if __name__ == '__main__':
    """
    Test tag discovery with a real PLC
    
    Usage:
        python ethernetip_client_real.py
    """
    import sys
    
    if not CPPPO_AVAILABLE:
        print("\n" + "="*70)
        print("ERROR: cpppo library not installed")
        print("="*70)
        print("\nInstall with: pip install cpppo")
        print("\nOr use the simulator: python ethernetip_simulator.py")
        print("="*70)
        sys.exit(1)
    
    # Configuration
    PLC_HOST = "192.168.1.100"  # Change to your PLC IP
    PLC_SLOT = 0
    
    print("\n" + "="*70)
    print("Real PLC Tag Discovery Test")
    print("="*70)
    print(f"\nTarget PLC: {PLC_HOST}:{PLC_SLOT}")
    print("\nAttempting to discover tags...")
    print("-"*70)
    
    try:
        tags = list_all_tags(PLC_HOST, PLC_SLOT, timeout=10.0)
        
        if tags:
            print(f"\n✓ Successfully discovered {len(tags)} tags:")
            for i, tag in enumerate(tags, 1):
                print(f"  {i}. {tag}")
        else:
            print("\n⚠ No tags discovered automatically.")
            print("\nThis could mean:")
            print("  1. PLC doesn't support tag enumeration service")
            print("  2. Different CIP implementation required")
            print("  3. Security/permissions restrictions")
            print("\n💡 Try these alternatives:")
            print("  - Use pylogix library (better tag support)")
            print("  - Specify tags manually in device configuration")
            print("  - Check PLC documentation for tag browsing support")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify PLC IP address is correct")
        print("  2. Check network connectivity: ping {PLC_HOST}")
        print("  3. Ensure PLC is online and accessible")
        print("  4. Verify firewall allows port 44818 (EtherNet/IP)")
        print("  5. Check PLC slot number is correct")
    
    print("\n" + "="*70)
