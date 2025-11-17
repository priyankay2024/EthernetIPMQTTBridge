"""
EthernetIP PLC Simulator
This script simulates an EthernetIP PLC device for testing purposes.
It uses a mock approach - modifying the app.py to use simulated data instead of real connections.

For a simpler testing approach, this file can be imported to provide mock data.
"""

import random
import time
from datetime import datetime


class MockEthernetIPClient:
    """
    Mock EthernetIP client that simulates tag reading without a real PLC.
    This replaces the cpppo.server.enip.client for testing purposes.
    """
    
    def __init__(self):
        self.tags = {
            'Tag1': 100.5,
            'Tag2': 25.3,
            'Tag3': 42,
            'Temperature': 72.5,
            'Pressure': 14.7,
            'Speed': 1500,
            'Status': 1,
            'Counter': 0,
            'Motor_Running': 1,
            'Voltage': 220.5
        }
        self.connected = False
        self.host = None
    
    def update_values(self):
        """Update tag values to simulate realistic changes"""
        self.tags['Tag1'] = round(100 + random.uniform(-5, 5), 2)
        self.tags['Tag2'] = round(25 + random.uniform(-2, 2), 2)
        self.tags['Tag3'] = random.randint(40, 45)
        self.tags['Temperature'] = round(72 + random.uniform(-1, 1), 2)
        self.tags['Pressure'] = round(14.7 + random.uniform(-0.5, 0.5), 2)
        self.tags['Speed'] = random.randint(1400, 1600)
        self.tags['Status'] = random.choice([0, 1])
        self.tags['Counter'] = (self.tags['Counter'] + 1) % 10000
        self.tags['Motor_Running'] = random.choice([0, 1])
        self.tags['Voltage'] = round(220 + random.uniform(-5, 5), 2)
    
    def connector(self, host, timeout=5.0):
        """Mock connector context manager"""
        self.host = host
        return self
    
    def __enter__(self):
        """Context manager entry"""
        self.connected = True
        print(f"[SIMULATOR] Connected to mock PLC at {self.host}")
        return self
    
    def __exit__(self, *args):
        """Context manager exit"""
        self.connected = False
        print(f"[SIMULATOR] Disconnected from mock PLC")
    
    def synchronous(self, operations):
        """
        Mock synchronous operation that returns simulated tag values.
        Yields data in the same format as cpppo's client.
        """
        # Update values to simulate live data
        self.update_values()
        
        # Parse the operations and return corresponding values
        for index, (descr, op) in enumerate(operations):
            tag_name = descr.strip()
            
            # Check if this tag exists in our simulated tags
            if tag_name in self.tags:
                value = self.tags[tag_name]
                status = True
            else:
                # Tag doesn't exist - return None
                value = None
                status = False
            
            # Yield in cpppo format: (index, description, operation, reply, status, value)
            yield (index, descr, op, None, status, value)
    
    @staticmethod
    def parse_operations(tags):
        """
        Mock parse_operations that returns operation descriptors.
        In real cpppo, this parses tag names into operations.
        """
        operations = []
        for tag in tags:
            tag = tag.strip()
            if tag:
                # Return tuple of (description, operation)
                operations.append((tag, None))
        return operations


# Singleton instance
_mock_client = MockEthernetIPClient()


def get_mock_client():
    """Get the singleton mock client instance"""
    return _mock_client


def connector(host, timeout=5.0):
    """Mock connector function that replaces cpppo.server.enip.client.connector"""
    return _mock_client.connector(host, timeout)


def parse_operations(tags):
    """Mock parse_operations function"""
    return MockEthernetIPClient.parse_operations(tags)


def list_all_tags(host, slot=0, timeout=5.0):
    """
    List all available tags from a PLC device.
    This simulates tag discovery functionality.
    
    Args:
        host: PLC IP address
        slot: PLC slot number
        timeout: Connection timeout
        
    Returns:
        list: List of available tag names
    """
    print(f"[SIMULATOR] Listing all tags from {host} (slot: {slot})")
    
    # In a real implementation with cpppo, this would:
    # 1. Connect to the PLC
    # 2. Use CIP services to enumerate all controller tags
    # 3. Return the list of tag names
    
    # For the simulator, return all available simulated tags
    client = get_mock_client()
    tags = list(client.tags.keys())
    
    print(f"[SIMULATOR] Found {len(tags)} tags: {', '.join(tags)}")
    return tags


if __name__ == '__main__':
    """Demonstrate the mock client"""
    print("=" * 70)
    print(" " * 20 + "EthernetIP Mock Client Demo")
    print("=" * 70)
    print()
    
    client = MockEthernetIPClient()
    
    print("Available simulated tags:")
    for tag_name, value in client.tags.items():
        print(f"  ✓ {tag_name}: {value}")
    print()
    
    print("Testing mock connection and tag reading...")
    print()
    
    # Simulate reading tags
    tags_to_read = ['Tag1', 'Tag2', 'Temperature', 'NonExistentTag']
    
    with client.connector('192.168.21.48') as connection:   # Change IP (host) as needed
        operations = client.parse_operations(tags_to_read)
        
        for index, descr, op, reply, status, value in connection.synchronous(operations):
            if status:
                print(f"  ✓ {descr}: {value}")
            else:
                print(f"  ✗ {descr}: Failed to read")
    
    print()
    print("Mock client demonstration complete!")
    print("=" * 70)
