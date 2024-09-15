from time import sleep

import sys
import serial
import configparser

# Serial Device
serial_device = '/dev/ttyUSB0'

# 瞬時電力計測値取得コマンドフレーム
echonetLiteFrame = b'\x10\x81\x00\x01\x05\xFF\x01\x02\x88\x01\x62\x01\xE7\x00'

# config init
inifile       = configparser.ConfigParser()
inifile.read('./conf.ini', 'utf-8')
Broute_id     = inifile.get('settings', 'broute_id')
Broute_pw     = inifile.get('settings', 'broute_pw')
Channel       = inifile.get('settings', 'channel')
PanId         = inifile.get('settings', 'panid')
Address       = inifile.get('settings', 'address')

# serial init
ser = serial.Serial(
    port=serial_device, 
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    rtscts=True,   #HWフロー制御
    xonxoff=False, #SWフロー制御
    timeout=2
)

# RTS/CTSのステータス確認
print("RTS:", ser.rts)
print("CTS:", ser.cts)

# SKRESET
ser.write(str.encode("SKRESET" + "\r\n"))
ser.readline() # エコーバック
print('SKRESET:', ser.readline().decode(encoding='utf-8'), end="")
sleep(1)

# SKSETPWD Broute passowrd
print('Setup Broute password')
ser.write(str.encode("SKSETPWD C " + Broute_pw + "\r\n"))
ser.readline()
print(ser.readline().decode(encoding='utf-8'), end="")

# SKSETRBID Broute ID
print('Setup Broute ID')
ser.write(str.encode("SKSETRBID " + Broute_id + "\r\n"))
ser.readline()
print(ser.readline().decode(encoding='utf-8'), end="")

# SKSREG S2 Channel
print('Setup Channel')
ser.write(str.encode("SKSREG S2 " + Channel + "\r\n"))
ser.readline()
print(ser.readline().decode(encoding='utf-8'), end="")

# SKSREG S3 PanID
print('Setup PanID')
ser.write(str.encode("SKSREG S3 " + PanId + "\r\n"))
ser.readline()
print(ser.readline().decode(encoding='utf-8'), end="")

# SKJOIN
print('SKJOIN')
ser.write(str.encode("SKJOIN " + Address + "\r\n"))
ser.readline()
print(ser.readline().decode(encoding='utf-8'), end="")

# wait PANA connection
bConnected = False
while not bConnected:
    line = ser.readline().decode(encoding='utf-8', errors='ignore')
    if line.startswith("EVENT 24"):
        print("PANA connect failed")
        sys.exit()
    elif line.startswith("EVENT 25"):
        print('PANA connect success')
        bConnected = True

ser.readline()

while True:
    # send ECHONET Lite Frame
    command = "SKSENDTO 1 {0} 0E1A 1 0 {1:04X} ".format(Address, len(echonetLiteFrame))
    ser.write(str.encode(command) + echonetLiteFrame )

    # debug
    # print('[debug:]', ser.readline()) # エコーバック
    # print('[debug]', ser.readline()) # EVENT 21
    # print('[debug]',ser.readline()) # OK

    # data read
    data = ser.readline()
    print(data)

    # data check
    if data.startswith(b"ERXUDP"):
        cols = data.strip().split(b' ')
        print('[debug cols]', cols)
        try:
            res = cols[9]
        except IndexError:
            print('[Skip] cols index error')
            continue
        print('[debug res]', res, res.hex(), len(res))
        seoj = res[4:4+3]
        # print('[debug seoj]', seoj.hex())
        esv = res[10:10+1]
        # print('[debug esv]', esv.hex())
        if seoj.hex() == "028801" and esv.hex() == "72":
            epc = res[12:12+1]
            # print('[epc]', epc.hex())
            # 瞬時電力計測値(E7)
            if epc.hex() == "e7":
                hex_watt = res[-2:].hex() # Last4byte瞬時電力?
                # print('[hex_watt]', hex_watt)
                watt = int(hex_watt, 16)
                if watt < 10:
                    print('[Skip] watt < 10')
                    continue
                print(u"瞬時電力計測値:{0}[W]".format(watt))
        else:
            print('[Skip] not ECHONET Lite Frame')

    sleep(60)

ser.close()
