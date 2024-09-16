import configparser
from time import sleep
from BP35C2.smart_meter import SmartMeter

def load_config(file_path):
    """Load configuration from file."""
    config = configparser.ConfigParser()
    config.read(file_path, 'utf-8')
    return config

def main():
    # Define parameters
    config_path = './conf.ini'
    serial_device = '/dev/ttyUSB0'
    sleep_interval = 30

    # Load configuration
    config = load_config(config_path)
    address = config.get('settings', 'address')

    # Initialize SmartMeter instance
    meter = SmartMeter(serial_device, 115200)

    # Setup Broute authentication and join network
    broute_pw = config.get('settings', 'broute_pw')
    broute_id = config.get('settings', 'broute_id')
    meter.setup_broute_auth(broute_pw, broute_id)
    meter.join_network(address)

    # Main loop
    while True:
        sm.get_current_watt(address)
        sleep(sleep_interval)

    meter.close()

if __name__ == '__main__':
    main()
