import sys
import serial
import configparser

# シリアルポートデバイス名
#serialPortDev = 'COM5'  # Windows の場合
serialPortDev = '/dev/ttyUSB0'  # Linuxの場合

# 設定情報読み出し
inifile       = configparser.ConfigParser()
inifile.read('./SmartMeter.ini', 'utf-8')
Broute_id     = inifile.get('settings', 'Broute_id')
Broute_pw     = inifile.get('settings', 'Broute_pw')

# シリアルポート初期化
ser = serial.Serial(serialPortDev, '115200')

# Bルート認証パスワード設定
print('Bルートパスワード設定')
ser.write(str.encode("SKSETPWD C " + Broute_pw + "\r\n"))
ser.readline()
print(ser.readline().decode(encoding='utf-8'), end="")  # 成功ならOKを返す

# Bルート認証ID設定
print('Bルート認証ID設定')
ser.write(str.encode("SKSETRBID " + Broute_id + "\r\n"))
ser.readline()
print(ser.readline().decode(encoding='utf-8'), end="")  # 成功ならOKを返す

scanDuration = 4 # スキャン時間
scanRes = {} # スキャン結果の入れ物

# アクティブスキャン
while ('Channel' not in scanRes):
    ser.write(str.encode("SKSCAN 2 FFFFFFFF " + str(scanDuration) + " 0" + "\r\n"))
    scanEnd = False
    while not scanEnd :
        line = ser.readline().decode(encoding='utf-8')
        if line.startswith("EVENT 22") :
            # スキャン終了
            scanEnd = True
        elif line.startswith("  ") :
            cols = line.strip().split(':')
            scanRes[cols[0]] = cols[1]
    scanDuration+=1

    if 7 < scanDuration and ('Channel' not in scanRes):
        print("スキャンリトライオーバー")
        sys.exit()

# Channel設定
print("Channel:" + scanRes["Channel"])
inifile.set('settings', 'Channel', scanRes["Channel"])

# Pan ID設定
print("PanID:" + scanRes["Pan ID"])
inifile.set('settings', 'PanId', scanRes["Pan ID"])

# MACアドレスをIPV6リンクローカルアドレスに変換
ser.write(str.encode("SKLL64 " + scanRes["Addr"] + "\r\n"))
ser.readline().decode(encoding='utf-8')
ipv6Addr = ser.readline().decode(encoding='utf-8').strip()
print("Address:" + ipv6Addr)
inifile.set('settings', 'Address', ipv6Addr)

with open('./SmartMeter.ini', 'w') as configfile:
    inifile.write(configfile)
