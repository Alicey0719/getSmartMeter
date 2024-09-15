import sys
import serial
import configparser
import logging
from time import sleep

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path, 'utf-8')
    return {
        'broute_id': config.get('settings', 'broute_id'),
        'broute_pw': config.get('settings', 'broute_pw'),
        'channel': config.get('settings', 'channel'),
        'panid': config.get('settings', 'panid'),
        'address': config.get('settings', 'address')
    }

def init_serial(device):
    return serial.Serial(
        port=device,
        baudrate=115200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        rtscts=True,
        xonxoff=False,
        timeout=2
    )

def send_command(ser, command):
    ser.write(str.encode(command + "\r\n"))
    return ser.readline().decode(encoding='utf-8')

def setup_broute(ser, config):
    logger.info('Sending SKRESET')
    logger.info('SKRESET: %s', send_command(ser, "SKRESET"))
    sleep(1)
    
    logger.info('Setting up Broute password')
    logger.info('Setup Broute password: %s', send_command(ser, f"SKSETPWD C {config['broute_pw']}"))
    
    logger.info('Setting up Broute ID')
    logger.info('Setup Broute ID: %s', send_command(ser, f"SKSETRBID {config['broute_id']}"))
    
    logger.info('Setting up Channel')
    logger.info('Setup Channel: %s', send_command(ser, f"SKSREG S2 {config['channel']}"))
    
    logger.info('Setting up PanID')
    logger.info('Setup PanID: %s', send_command(ser, f"SKSREG S3 {config['panid']}"))

def join_network(ser, address):
    logger.info('Attempting SKJOIN')
    logger.info('SKJOIN: %s', send_command(ser, f"SKJOIN {address}"))
    while True:
        line = ser.readline().decode(encoding='utf-8', errors='ignore')
        if line.startswith("EVENT 24"):
            logger.error("PANA connect failed")
            sys.exit()
        elif line.startswith("EVENT 25"):
            logger.info('PANA connect success')
            break

def read_echonet_lite(ser, address, echonet_lite_frame):
    command = f"SKSENDTO 1 {address} 0E1A 1 0 {len(echonet_lite_frame):04X} "
    ser.write(str.encode(command) + echonet_lite_frame)

    data = ser.readline()
    if data.startswith(b"ERXUDP"):
        handle_echonet_response(data)

def handle_echonet_response(data):
    cols = data.strip().split(b' ')
    try:
        res = cols[9]
    except IndexError:
        logger.warning('[Skip] cols index error')
        return
    seoj = res[4:7]
    esv = res[10:11]
    if seoj.hex() == "028801" and esv.hex() == "72":
        epc = res[12:13]
        if epc.hex() == "e7":
            hex_watt = res[-2:].hex()
            watt = int(hex_watt, 16)
            if watt >= 10:
                logger.info(f"瞬時電力計測値: {watt} [W]")
            else:
                logger.info('[Skip] watt < 10')
    else:
        logger.info('[Skip] not ECHONET Lite Frame')

def main():
    # Define parameters
    config_path = './conf.ini'
    serial_device = '/dev/ttyUSB0'
    echonet_lite_frame = b'\x10\x81\x00\x01\x05\xFF\x01\x02\x88\x01\x62\x01\xE7\x00'
    sleep_interval = 60

    # Load configuration and initialize serial
    config = load_config(config_path)
    ser = init_serial(serial_device)
    
    logger.info("RTS: %s", ser.rts)
    logger.info("CTS: %s", ser.cts)
    
    setup_broute(ser, config)
    join_network(ser, config['address'])

    # Main loop
    while True:
        read_echonet_lite(ser, config['address'], echonet_lite_frame)
        sleep(sleep_interval)

    ser.close()

if __name__ == '__main__':
    main()
