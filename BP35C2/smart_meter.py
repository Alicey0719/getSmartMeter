import sys
import serial
import logging
from time import sleep

# Setup logging for smart_meter
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartMeter:
    def __init__(self, serial_port, baudrate):
        """Initialize the SmartMeter class."""
        self.ser = self.initialize_serial(serial_port, baudrate)
        logger.debug('SKRESET: %s', self.send_command('SKRESET'))
        sleep(1)

    def initialize_serial(self, serial_port, baudrate):
        """Initialize the serial port."""
        ser = serial.Serial(serial_port, baudrate)
        logger.debug("RTS: %s", ser.rts)
        logger.debug("CTS: %s", ser.cts)
        return ser

    def send_command(self, command, ignore_echoback=True):
        """Send a command to the serial port and read the response."""
        self.ser.write(str.encode(command + "\r\n"))
        if ignore_echoback:
            self.ser.readline()  # Skip the echoback
        return self.ser.readline().decode(encoding='utf-8').strip()

    def setup_broute_auth(self, broute_pw, broute_id):
        """Set up Broute authentication."""
        r = self.send_command(f"SKSETPWD C {broute_pw}")
        logger.debug(f'Setting up Broute password: {r}')
        
        r = self.send_command(f"SKSETRBID {broute_id}")
        logger.debug(f'Setting up Broute ID: {r}')

    def setup_channel(self, channel):
        logger.debug("Setting up Channel: %s", self.send_command(f"SKSREG S2 {channel}"))

    def setup_panid(self, panid):
        logger.debug("Setting up PanID: %s", self.send_command(f"SKSREG S3 {panid}"))

    def scan_for_channels(self, max_duration):
        """Perform an active scan for channels and return scan results."""
        scan_duration = 4
        scan_results = {}
        
        while 'Channel' not in scan_results:
            self.send_command(f"SKSCAN 2 FFFFFFFF {scan_duration} 0")
            scan_end = False
            
            while not scan_end:
                line = self.ser.readline().decode(encoding='utf-8')
                if line.startswith("EVENT 22"):
                    scan_end = True
                elif line.startswith("  "):
                    cols = line.strip().split(':')
                    if len(cols) == 2:
                        scan_results[cols[0]] = cols[1]

            scan_duration += 1
            if scan_duration > max_duration and 'Channel' not in scan_results:
                logger.error("Scan retry limit exceeded")
                sys.exit()

        return scan_results

    def convert_mac_to_ipv6(self, mac_addr):
        """Convert MAC address to IPv6 link-local address."""
        self.send_command(f"SKLL64 {mac_addr}", ignore_echoback=False)
        return self.ser.readline().decode(encoding='utf-8').strip()

    def join_network(self, address):
        """Join the network using the provided address."""
        logger.debug('SKJOIN: %s', self.send_command(f"SKJOIN {address}"))
        while True:
            line = self.ser.readline().decode(encoding='utf-8', errors='ignore')
            if line.startswith("EVENT 24"):
                logger.error("PANA connect failed")
                sys.exit()
            elif line.startswith("EVENT 25"):
                logger.info('PANA connect success')
                break

    def get_current_watt(self, address):
        """Get the current wattage from the smart meter."""
        echonet_lite_frame = b'\x10\x81\x00\x01\x05\xFF\x01\x02\x88\x01\x62\x01\xE7\x00'
        return self.read_echonet_lite(address, echonet_lite_frame)

    def read_echonet_lite(self, address, echonet_lite_frame):
        """Send and receive an Echonet Lite frame."""
        command = f"SKSENDTO 1 {address} 0E1A 1 0 {len(echonet_lite_frame):04X} "
        self.ser.write(str.encode(command) + echonet_lite_frame)

        while True:
            data = self.ser.readline()
            if data.startswith(b"ERXUDP"):
                res = self.handle_echonet_response(data)
                if type(res) is int:
                    return res

    def handle_echonet_response(self, data):
        """Handle the response from an Echonet Lite frame."""
        cols = data.strip().split(b' ')
        try:
            res = cols[9]
        except IndexError:
            logger.warning('[Skip] cols index error')
            return False
        seoj = res[4:7]
        esv = res[10:11]
        if seoj.hex() == "028801" and esv.hex() == "72":
            epc = res[12:13]
            if epc.hex() == "e7":
                hex_watt = res[-2:].hex()
                watt = int(hex_watt, 16)
                if watt >= 10: # なぜか3Wを返すことがあるため対策
                    # logger.info(f"瞬時電力計測値: {watt} [W]")
                    return watt
                else:
                    logger.info('[Skip] watt < 10')
                    return False
        else:
            logger.info('[Skip] not ECHONET Lite Frame')
            return False

    def close(self):
        self.ser.close()
