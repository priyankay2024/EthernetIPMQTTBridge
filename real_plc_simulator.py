"""
Real EthernetIP PLC Simulator Server
Simulates an actual EthernetIP/CIP device that listens on a network port.
You can run multiple instances on different ports to test multiple device connections.

Usage:
    python real_plc_simulator.py --port 44818 --name PLC-1
    python real_plc_simulator.py --port 44819 --name PLC-2
    python real_plc_simulator.py --port 44820 --name PLC-3
"""

import socket
import threading
import random
import time
import argparse
import struct
from datetime import datetime


class EthernetIPSimulator:
    """
    Simulates an EthernetIP/CIP device that responds to tag read requests.
    """
    
    def __init__(self, host='127.0.0.1', port=44818, name='PLC-Simulator'):
        self.host = host
        self.port = port
        self.name = name
        self.running = False
        self.server_socket = None
        self.clients = []
        
        # Simulated tag database with different data types
        self.tags = {
            # Generic tags
            'Tag1': {'type': 'REAL', 'value': 100.5},
            'Tag2': {'type': 'REAL', 'value': 25.3},
            'Tag3': {'type': 'DINT', 'value': 42},
            
            # Process variables
            'Temperature': {'type': 'REAL', 'value': 72.5},
            'Pressure': {'type': 'REAL', 'value': 14.7},
            'Speed': {'type': 'DINT', 'value': 1500},
            
            # Status tags
            'Status': {'type': 'BOOL', 'value': True},
            'Counter': {'type': 'DINT', 'value': 0},
            'Motor_Running': {'type': 'BOOL', 'value': True},
            'Voltage': {'type': 'REAL', 'value': 220.5},
            
            # Additional tags for variety
            'Flow_Rate': {'type': 'REAL', 'value': 45.2},
            'Alarm': {'type': 'BOOL', 'value': False},
            'Production_Count': {'type': 'DINT', 'value': 1234},
        }
        
        # Thread for updating tag values
        self.update_thread = None
    
    def update_tag_values(self):
        """Continuously update tag values to simulate live data"""
        while self.running:
            try:
                # Update REAL type tags with small variations
                self.tags['Tag1']['value'] = round(100 + random.uniform(-5, 5), 2)
                self.tags['Tag2']['value'] = round(25 + random.uniform(-2, 2), 2)
                self.tags['Temperature']['value'] = round(72 + random.uniform(-3, 3), 2)
                self.tags['Pressure']['value'] = round(14.7 + random.uniform(-0.5, 0.5), 2)
                self.tags['Voltage']['value'] = round(220 + random.uniform(-10, 10), 2)
                self.tags['Flow_Rate']['value'] = round(45 + random.uniform(-5, 5), 2)
                
                # Update DINT type tags
                self.tags['Tag3']['value'] = random.randint(40, 45)
                self.tags['Speed']['value'] = random.randint(1400, 1600)
                self.tags['Counter']['value'] = (self.tags['Counter']['value'] + 1) % 10000
                self.tags['Production_Count']['value'] = (self.tags['Production_Count']['value'] + random.randint(0, 5)) % 100000
                
                # Update BOOL type tags
                self.tags['Status']['value'] = random.choice([True, False, True])  # Bias towards True
                self.tags['Motor_Running']['value'] = random.choice([True, True, False])  # Bias towards True
                self.tags['Alarm']['value'] = random.choice([False, False, False, True])  # Bias towards False
                
                time.sleep(1)  # Update every second
            except Exception as e:
                print(f"[{self.name}] Error updating tags: {e}")
    
    def handle_client(self, client_socket, address):
        """Handle incoming client connection"""
        print(f"[{self.name}] Client connected from {address}")
        self.clients.append(client_socket)
        
        try:
            while self.running:
                # Receive data from client
                data = client_socket.recv(4096)
                if not data:
                    break
                
                # Parse request and send response
                response = self.process_request(data)
                if response:
                    client_socket.sendall(response)
                    
        except Exception as e:
            print(f"[{self.name}] Client error: {e}")
        finally:
            print(f"[{self.name}] Client disconnected from {address}")
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
    
    def process_request(self, data):
        """
        Process EthernetIP/CIP request and generate response.
        This is a simplified implementation that responds to cpppo's requests.
        """
        try:
            # In a real implementation, you'd parse CIP packets properly
            # For simplicity, we'll create a basic response
            
            # EthernetIP Encapsulation Header (24 bytes minimum)
            # Command: 0x006F (SendRRData)
            # Length: variable
            # Session Handle: echo from request
            # Status: 0x00000000 (success)
            # Context: echo from request
            # Options: 0x00000000
            
            # For this simulator, we'll send back a simple success response
            # that indicates the tag read was successful
            
            response = bytearray()
            
            # EIP Header
            response.extend(b'\x6F\x00')  # Command: SendRRData
            response.extend(b'\x00\x00')  # Length (will be updated)
            response.extend(b'\x01\x00\x00\x00')  # Session Handle
            response.extend(b'\x00\x00\x00\x00')  # Status: Success
            response.extend(b'\x00' * 8)  # Sender Context
            response.extend(b'\x00\x00\x00\x00')  # Options
            
            # CPF Items (Common Packet Format)
            # Item Count
            response.extend(b'\x02\x00')  # 2 items
            
            # Address Item
            response.extend(b'\x00\x00')  # Type ID: Null Address
            response.extend(b'\x00\x00')  # Length: 0
            
            # Data Item
            response.extend(b'\xB2\x00')  # Type ID: Unconnected Data Item
            response.extend(b'\x08\x00')  # Length: 8 bytes
            
            # CIP Response
            response.extend(b'\x00')  # Service: Read Tag Response (0x4C | 0x80 = 0xCC, but simplified)
            response.extend(b'\x00')  # Reserved
            response.extend(b'\x00')  # General Status: Success
            response.extend(b'\x00')  # Extended Status Size
            
            # Tag value (simplified - just return a dummy value)
            response.extend(struct.pack('<f', 123.45))  # Float value
            
            # Update length field
            data_length = len(response) - 24
            response[2:4] = struct.pack('<H', data_length)
            
            return bytes(response)
            
        except Exception as e:
            print(f"[{self.name}] Error processing request: {e}")
            return None
    
    def start(self):
        """Start the simulator server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            print("=" * 80)
            print(f"  {self.name} - EthernetIP Simulator Server")
            print("=" * 80)
            print(f"  Listening on: {self.host}:{self.port}")
            print(f"  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            print("  Available Tags:")
            for tag_name, tag_data in sorted(self.tags.items()):
                print(f"    ✓ {tag_name:20} [{tag_data['type']:4}] = {tag_data['value']}")
            print()
            print("  Waiting for connections... (Press Ctrl+C to stop)")
            print("=" * 80)
            print()
            
            # Start tag update thread
            self.update_thread = threading.Thread(target=self.update_tag_values, daemon=True)
            self.update_thread.start()
            
            # Accept client connections
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    client_socket, address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[{self.name}] Accept error: {e}")
                    
        except Exception as e:
            print(f"[{self.name}] ERROR: Failed to start simulator: {e}")
            if "Address already in use" in str(e) or "10048" in str(e):
                print(f"[{self.name}] Port {self.port} is already in use!")
                print(f"[{self.name}] Try a different port or close the existing process.")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the simulator server"""
        print(f"\n[{self.name}] Shutting down...")
        self.running = False
        
        # Close all client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print(f"[{self.name}] Stopped.")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='EthernetIP PLC Simulator Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start default simulator on port 44818
  python real_plc_simulator.py
  
  # Start multiple simulators on different ports
  python real_plc_simulator.py --port 44818 --name PLC-1
  python real_plc_simulator.py --port 44819 --name PLC-2
  python real_plc_simulator.py --port 44820 --name PLC-3
  
  # Start on specific host and port
  python real_plc_simulator.py --host 0.0.0.0 --port 44818 --name Factory-PLC
        """
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host IP address to bind to (default: 127.0.0.1, use 0.0.0.0 for all interfaces)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=44818,
        help='Port number to listen on (default: 44818)'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        default='PLC-Simulator',
        help='Name of this simulator instance (default: PLC-Simulator)'
    )
    
    args = parser.parse_args()
    
    # Create and start simulator
    simulator = EthernetIPSimulator(host=args.host, port=args.port, name=args.name)
    
    try:
        simulator.start()
    except KeyboardInterrupt:
        print("\n\nReceived shutdown signal...")
        simulator.stop()


if __name__ == '__main__':
    main()
