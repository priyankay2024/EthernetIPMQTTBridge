"""
EthernetIP Tag Discovery using PyLogix

PyLogix has excellent built-in tag enumeration for Allen-Bradley PLCs.
This is the RECOMMENDED approach for production use with real PLCs.

Installation:
    pip install pylogix
"""

try:
    from pylogix import PLC
    PYLOGIX_AVAILABLE = True
except ImportError:
    PYLOGIX_AVAILABLE = False
    print("WARNING: pylogix not available. Install with: pip install pylogix")


def list_all_tags(host, slot=0, timeout=5.0):
    """
    List all tags from an Allen-Bradley PLC using pylogix.
    
    This is the most reliable method for tag discovery on AB PLCs.
    Works with ControlLogix, CompactLogix, Micro800, and other AB controllers.
    
    Args:
        host: PLC IP address
        slot: PLC slot number (pylogix handles routing automatically)
        timeout: Connection timeout in seconds
        
    Returns:
        list: List of tag names (strings)
    """
    if not PYLOGIX_AVAILABLE:
        raise Exception("pylogix library not installed. Install with: pip install pylogix")
    
    print(f"[TAG DISCOVERY] Connecting to PLC at {host} using pylogix...")
    
    try:
        # Create PLC connection
        plc = PLC()
        plc.IPAddress = host
        plc.ProcessorSlot = slot
        plc.SocketTimeout = timeout
        
        # Get all tags from the controller
        tag_list = plc.GetTagList()
        
        if tag_list.Value is None:
            error_msg = f"Pylogix: Failed to get tag list: {tag_list.Status}"
            print(f"[TAG DISCOVERY] {error_msg}")
            raise Exception(error_msg)
        
        # Extract tag names
        tags = []
        for tag in tag_list.Value:
            tag_name = tag.TagName
            
            # Filter out system tags (start with underscore)
            if not tag_name.startswith('_'):
                tags.append(tag_name)
                print(f"[TAG DISCOVERY]   Found: {tag_name} (Type: {tag.DataType})")
        
        # Close connection
        plc.Close()
        
        print(f"[TAG DISCOVERY] Successfully discovered {len(tags)} tags")
        return sorted(tags)
        
    except Exception as e:
        error_msg = f"Error discovering tags from {host}: {str(e)}"
        print(f"[TAG DISCOVERY] {error_msg}")
        raise Exception(error_msg)


def list_program_tags(host, program_name, slot=0, timeout=5.0):
    """
    List tags from a specific program in the PLC.
    
    Args:
        host: PLC IP address
        program_name: Name of the program (e.g., "MainProgram")
        slot: PLC slot number
        timeout: Connection timeout
        
    Returns:
        list: Program-scoped tag names
    """
    if not PYLOGIX_AVAILABLE:
        raise Exception("pylogix library not installed")
    
    print(f"[TAG DISCOVERY] Getting tags from program '{program_name}'...")
    
    try:
        plc = PLC()
        plc.IPAddress = host
        plc.ProcessorSlot = slot
        plc.SocketTimeout = timeout
        
        # Get program tags
        tag_list = plc.GetProgramTagList(program_name)
        
        if tag_list.Value is None:
            raise Exception(f"Failed to get program tags: {tag_list.Status}")
        
        tags = [tag.TagName for tag in tag_list.Value]
        
        plc.Close()
        
        print(f"[TAG DISCOVERY] Found {len(tags)} tags in program '{program_name}'")
        return sorted(tags)
        
    except Exception as e:
        print(f"[TAG DISCOVERY] Error: {e}")
        raise


def get_tag_info(host, tag_name, slot=0):
    """
    Get detailed information about a specific tag.
    
    Returns:
        dict: Tag information including data type, value, etc.
    """
    if not PYLOGIX_AVAILABLE:
        raise Exception("pylogix library not installed")
    
    plc = PLC()
    plc.IPAddress = host
    plc.ProcessorSlot = slot
    
    try:
        result = plc.Read(tag_name)
        plc.Close()
        
        return {
            'name': tag_name,
            'value': result.Value,
            'type': result.TagName,
            'status': result.Status
        }
    except Exception as e:
        plc.Close()
        raise Exception(f"Error reading tag {tag_name}: {e}")


# Wrapper functions for compatibility with existing code
def connector(host, timeout=5.0):
    """
    Context manager for PLC connection (pylogix style).
    Returns a PLC object that can be used to read/write tags.
    """
    if not PYLOGIX_AVAILABLE:
        raise Exception("pylogix not available")
    
    class PLCConnection:
        def __init__(self, host, timeout):
            self.plc = PLC()
            self.plc.IPAddress = host
            self.plc.SocketTimeout = timeout
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            self.plc.Close()
            
        def synchronous(self, operations):
            """
            Read tags synchronously (compatible with cpppo-style code).
            
            operations: List of (tag_name, operation) tuples
            """
            for index, (tag_name, op) in enumerate(operations):
                result = self.plc.Read(tag_name)
                
                status = result.Status == "Success"
                value = result.Value if status else None
                
                yield (index, tag_name, op, None, status, value)
    
    return PLCConnection(host, timeout)


def parse_operations(tags):
    """
    Parse tag list into operations format.
    Compatible with both cpppo and pylogix approaches.
    """
    return [(tag, None) for tag in tags]


if __name__ == '__main__':
    """Test tag discovery with real PLC using pylogix"""
    import sys
    
    if not PYLOGIX_AVAILABLE:
        print("\n" + "="*70)
        print("ERROR: pylogix library not installed")
        print("="*70)
        print("\nInstall with:")
        print("  pip install pylogix")
        print("\nOr use the simulator:")
        print("  python ethernetip_simulator.py")
        print("="*70)
        sys.exit(1)
    
    # Configuration - CHANGE THESE
    PLC_HOST = "192.168.1.100"  # Your PLC IP address
    PLC_SLOT = 0                 # Processor slot (usually 0)
    
    print("\n" + "="*70)
    print("PyLogix Tag Discovery Test")
    print("="*70)
    print(f"\nTarget PLC: {PLC_HOST}")
    print(f"Slot: {PLC_SLOT}")
    print("\nAttempting to discover tags...")
    print("-"*70 + "\n")
    
    try:
        # Discover all controller-scoped tags
        tags = list_all_tags(PLC_HOST, PLC_SLOT, timeout=10.0)
        
        print("\n" + "-"*70)
        print(f"✓ SUCCESS! Discovered {len(tags)} tags:")
        print("-"*70)
        
        for i, tag in enumerate(tags, 1):
            print(f"  {i:3d}. {tag}")
        
        # Test reading a few tags
        if tags:
            print("\n" + "-"*70)
            print("Testing tag reads (first 3 tags):")
            print("-"*70)
            
            with connector(PLC_HOST, timeout=5.0) as conn:
                operations = parse_operations(tags[:3])
                
                for idx, tag, op, rpy, sts, val in conn.synchronous(operations):
                    if sts:
                        print(f"  ✓ {tag}: {val}")
                    else:
                        print(f"  ✗ {tag}: Read failed")
        
        print("\n" + "="*70)
        print("✓ Tag discovery working correctly!")
        print("="*70)
        
    except Exception as e:
        print("\n" + "="*70)
        print("✗ ERROR")
        print("="*70)
        print(f"\n{e}\n")
        print("Troubleshooting:")
        print("  1. Verify PLC IP address is correct")
        print("  2. Check network: ping " + PLC_HOST)
        print("  3. Ensure PLC is online")
        print("  4. Check firewall allows port 44818")
        print("  5. Verify PLC supports EtherNet/IP")
        print("="*70)
