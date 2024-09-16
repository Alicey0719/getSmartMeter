import configparser
from BP35C2.smart_meter import SmartMeter

def load_config(file_path):
    """Load configuration from file."""
    config = configparser.ConfigParser()
    config.read(file_path, 'utf-8')
    return config

def update_config(config, settings, file_path):
    """Update configuration file with new settings."""
    for key, value in settings.items():
        config.set('settings', key, value)

    with open(file_path, 'w') as configfile:
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

    # Initialize SmartMeter instance
    sm = SmartMeter(serial_port, baudrate)

    # Setup Broute authentication
    sm.setup_broute_auth(broute_pw, broute_id)

    # Scan for channels
    scan_results = sm.scan_for_channels(max_scan_duration)

    # Update configuration with scan results
    settings = {
        'Channel': scan_results.get("Channel", "Unknown"),
        'PanId': scan_results.get("Pan ID", "Unknown"),
        'Address': sm.convert_mac_to_ipv6(scan_results.get("Addr", "Unknown"))
    }
    sm.close()

    print(f"Channel: {settings['Channel']}")
    print(f"PanID: {settings['PanId']}")
    print(f"Address: {settings['Address']}")
    update_config(config, settings)


if __name__ == '__main__':
    main()
