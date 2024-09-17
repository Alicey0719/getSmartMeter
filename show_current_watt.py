import logging
import configparser
from time import sleep
from BP35C2.smart_meter import SmartMeter

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config(file_path):
    """Load configuration from file."""
    config = configparser.ConfigParser()
    config.read(file_path, "utf-8")
    return config


def main():
    # Define parameters
    config_path = "./conf.ini"
    serial_device = "/dev/ttyUSB0"
    sleep_interval = 60

    # Load configuration
    config = load_config(config_path)
    broute_pw = config.get("settings", "broute_pw")
    broute_id = config.get("settings", "broute_id")
    panid = config.get("settings", "panid")
    channel = config.get("settings", "channel")
    address = config.get("settings", "address")

    # Initialize SmartMeter instance
    sm = SmartMeter(serial_device, 115200)

    # Setup Broute authentication and join network
    sm.setup_broute_auth(broute_pw, broute_id)
    sm.setup_channel(channel)
    sm.setup_panid(panid)

    sm.join_network(address)

    while True:
        watt = sm.get_current_watt(address)
        if type(watt) is not int:
            continue
        logging.info("Current Watt: %s[W]", watt)
        sleep(sleep_interval)

    # sm.close()


if __name__ == "__main__":
    main()
