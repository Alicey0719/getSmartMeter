from time import sleep

import sys
import serial
import configparser

# シリアルポートデバイス名
serialPortDev = '/dev/ttyUSB0'  # Linuxの場合

# 瞬時電力計測値取得コマンドフレーム
echonetLiteFrame = b'\x10\x81\x00\x01\x05\xFF\x01\x02\x88\x01\x62\x01\xE7\x00'

# 設定情報読み出し
inifile       = configparser.ConfigParser()
inifile.read('./SmartMeter.ini', 'utf-8')
Broute_id     = inifile.get('settings', 'broute_id')
Broute_pw     = inifile.get('settings', 'broute_pw')
Channel       = inifile.get('settings', 'channel')
PanId         = inifile.get('settings', 'panid')
Address       = inifile.get('settings', 'address')

# シリアルポート初期化
ser = serial.Serial(
    port=serialPortDev, 
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
time.sleep(1)

# Bルート認証パスワード設定
print('Bルートパスワード設定')
ser.write(str.encode("SKSETPWD C " + Broute_pw + "\r\n"))
ser.readline() # エコーバック
print(ser.readline().decode(encoding='utf-8'), end="")  # 成功ならOKを返す

# Bルート認証ID設定
print('Bルート認証ID設定')
ser.write(str.encode("SKSETRBID " + Broute_id + "\r\n"))
ser.readline() # エコーバック
print(ser.readline().decode(encoding='utf-8'), end="") # 成功ならOKを返す

# Channel設定
print('Channel設定')
ser.write(str.encode("SKSREG S2 " + Channel + "\r\n"))
ser.readline()  # エコーバック
print(ser.readline().decode(encoding='utf-8'), end="")  # 成功ならOKを返す

# PanID設定
print('PanID設定')
ser.write(str.encode("SKSREG S3 " + PanId + "\r\n"))
ser.readline() # エコーバック
print(ser.readline().decode(encoding='utf-8'), end="") # 成功ならOKを返す

# PANA 接続シーケンス
print('PANA接続シーケンス')
ser.write(str.encode("SKJOIN " + Address + "\r\n"))
ser.readline()  # エコーバック
print(ser.readline().decode(encoding='utf-8'), end="") # 成功ならOKを返す

# PANA 接続完了待ち
bConnected = False
while not bConnected :
    line = ser.readline().decode(encoding='utf-8', errors='ignore')
    if line.startswith("EVENT 24") :
        print("PANA 接続失敗")
        sys.exit() #接続失敗した時は終了
    elif line.startswith("EVENT 25") :
        print('PANA 接続成功')
        bConnected = True

ser.readline() #インスタンスリストダミーリード

while True:
    # コマンド送信
    # echonetLiteFrame=bytes.fromhex('1081000105ff010288016205d300e000e100e700e800')
    # print(echonetLiteFrame)
    command = "SKSENDTO 1 {0} 0E1A 1 0 {1:04X} ".format(Address, len(echonetLiteFrame))
    # ser.write(str.encode(command) + str.encode(echonetLiteFrame.hex().upper()) )
    # ser.write(str.encode(command) + bytes.fromhex('1081000105ff010288016205d300e000e100e700e800') )
    ser.write(str.encode(command) + echonetLiteFrame )

    #コマンド受信
    # print('aaa')
    # print('[debug:]', ser.readline()) # エコーバック
    # print('bbb')
    # print('[debug]', ser.readline()) # EVENT 21
    # print('ccc')
    # print('[debug]',ser.readline()) # 成功ならOKを返す
    # print('ddd')

    # 返信データ取得
    Data = ser.readline()
    # print('eeee')
    print(Data)

    # データチェック
    if Data.startswith(b"ERXUDP"):
        # print('fff')
        cols = Data.strip().split(b' ')
        print('[debug cols]', cols)
        res = cols[9]  # UDP受信データ部分
        print('[debug res]', res, res.hex(), len(res))
        seoj = res[4:4+3]
        # print('[debug seoj]', seoj.hex())
        ESV = res[10:10+1]
        # print('[debug ESV]', ESV.hex())
        # スマートメーター(028801)から来た応答(72)なら
        if seoj.hex() == "028801" and ESV.hex() == "72" :
            # print('ggg')
            EPC = res[12:12+1]
            # print('[EPC]', EPC.hex())
            # 瞬時電力計測値(E7)なら
            if EPC.hex() == "e7" :
                hexPower = res[-2:].hex() # 最後の4バイトが瞬時電力計測値
                # print('[hexPower]', hexPower)
                intPower = int(hexPower, 16)
                print(u"瞬時電力計測値:{0}[W]".format(intPower))
        else:
            print('[Skip]')

    sleep(60)

# ガード処理
ser.close()
