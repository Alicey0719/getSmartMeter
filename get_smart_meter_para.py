import sys
import serial
import configparser

def load_config(file_path):
    """Load configuration from file."""
    config = configparser.ConfigParser()
    config.read(file_path, 'utf-8')
    return config

def initialize_serial(port, baudrate):
    """Initialize the serial port."""
    return serial.Serial(port, baudrate)

def send_command(ser, command):
    """Send a command to the serial port and read the response."""
    ser.write(str.encode(command + "\r\n"))
    response = ser.readline().decode(encoding='utf-8').strip()
    return response

def setup_broute_auth(ser, broute_pw, broute_id):
    """Set up Broute authentication."""
    print('Setting up Broute password')
    send_command(ser, f"SKSETRBID {broute_id}")
    print(ser.readline().decode(encoding='utf-8').strip())
    
    print('Setting up Broute ID')
    send_command(ser, f"SKSETRBID {broute_id}")
    print(ser.readline().decode(encoding='utf-8').strip())


def scan_for_channels(ser, max_duration):
    """Perform an active scan for channels and return scan results."""
    scan_duration = 4
    scan_results = {}
    
    while 'Channel' not in scan_results:
        send_command(ser, f"SKSCAN 2 FFFFFFFF {scan_duration} 0")
        scan_end = False
        
        while not scan_end:
            line = ser.readline().decode(encoding='utf-8')
            if line.startswith("EVENT 22"):
                scan_end = True
            elif line.startswith("  "):
                cols = line.strip().split(':')
                if len(cols) == 2:
                    scan_results[cols[0]] = cols[1]

        scan_duration += 1
        if scan_duration > max_duration and 'Channel' not in scan_results:
            print("Scan retry limit exceeded")
            sys.exit()

    return scan_results

def convert_mac_to_ipv6(ser, mac_addr):
    """Convert MAC address to IPv6 link-local address."""
    send_command(ser, f"SKLL64 {mac_addr}")
    return ser.readline().decode(encoding='utf-8').strip()

def update_config(config, settings):
    """Update configuration file with new settings."""
    for key, value in settings.items():
        config.set('settings', key, value)

    with open('./conf.ini', 'w') as configfile:
        config.write(configfile)

def main():
    # Configuration
    serial_port = '/dev/ttyUSB0'
    baudrate = '115200'
    config_file = './conf.ini'
    max_scan_duration = 7

    # Load configuration
    config = load_config(config_file)
    broute_id = config.get('settings', 'Broute_id')
    broute_pw = config.get('settings', 'Broute_pw')

    # Initialize serial port
    ser = initialize_serial(serial_port, baudrate)

    # Setup Broute authentication
    setup_broute_auth(ser, broute_pw, broute_id)

    # Scan for channels
    scan_results = scan_for_channels(ser, max_scan_duration)

    # Update configuration with scan results
    settings = {
        'Channel': scan_results.get("Channel", "Unknown"),
        'PanId': scan_results.get("Pan ID", "Unknown"),
        'Address': convert_mac_to_ipv6(ser, scan_results.get("Addr", "Unknown"))
    }
    print(f"Channel: {settings['Channel']}")
    print(f"PanID: {settings['PanId']}")
    print(f"Address: {settings['Address']}")
    update_config(config, settings)

    ser.close()

if __name__ == '__main__':
    main()
