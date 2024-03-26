import asyncio
import logging

from bleak import BleakClient

# 讀取 H2U 體重計 LS102-B
# DE387D88-BDD7-920B-49BE-B3615C8A0719: 0102B 00000000
# F5:FC:3F:76:90:C4: 0102B 00000000
# ---------------------------------
# AdvertisementData(local_name='0102B 00000000', service_uuids=['000078a2-0000-1000-8000-00805f9b34fb'], rssi=-62)
# Service: 0000180a-0000-1000-8000-00805f9b34fb
#   Characteristic: 00002a25-0000-1000-8000-00805f9b34fb DEVICEINFO_SERVICE_SERIAL_NUMBER_CHARACTERISTIC_UUID
#   Characteristic: 00002a27-0000-1000-8000-00805f9b34fb DEVICEINFO_SERVICE_HARDWARE_REVISION_CHARACTERISTIC_UUID
#   Characteristic: 00002a26-0000-1000-8000-00805f9b34fb DEVICEINFO_SERVICE_FIRMWARE_REVISION_CHARACTERISTIC_UUID
#   Characteristic: 00002a29-0000-1000-8000-00805f9b34fb DEVICEINFO_SERVICE_MANUFACTURER_CHARACTERISTIC_UUID
#   Characteristic: 00002a28-0000-1000-8000-00805f9b34fb DEVICEINFO_SERVICE_SOFTWARE_REVISION_CHARACTERISTIC_UUID
# Service: 000078a2-0000-1000-8000-00805f9b34fb WEIGHT_SERVICE
#   Characteristic: 00008a21-0000-1000-8000-00805f9b34fb WEIGHT_MEASUREMENT
#   Characteristic: 00008a22-0000-1000-8000-00805f9b34fb WEIGHT_SCLAE_APPEND_MEASUREMENT_CHARACTERISTIC_UUID
#   Characteristic: 00008a20-0000-1000-8000-00805f9b34fb WEIGHT_SCLAE_FEATURE_CHARACTERISTIC_UUID
#   Characteristic: 00008a81-0000-1000-8000-00805f9b34fb WEIGHT_PASSWORD
#   Characteristic: 00008a82-0000-1000-8000-00805f9b34fb UPLOAD_INFORMATION_OR_EVENT_CHARACTERISTIC_UUID
# 
# [Service] 0000180a-0000-1000-8000-00805f9b34fb (Handle: 9): Device Information
#   [Characteristic] 00002a25-0000-1000-8000-00805f9b34fb (Handle: 10): Serial Number String (read), Value: bytearray(b'C490763FFCF5')
#     [Descriptor] 00002904-0000-1000-8000-00805f9b34fb (Handle: 12): Characteristic Presentation Format, Value: bytearray(b'\x19\x00\x00\x00\x01\x00\x00')
#   [Characteristic] 00002a27-0000-1000-8000-00805f9b34fb (Handle: 13): Hardware Revision String (read), Value: bytearray(b'B2')
#     [Descriptor] 00002904-0000-1000-8000-00805f9b34fb (Handle: 15): Characteristic Presentation Format, Value: bytearray(b'\x19\x00\x00\x00\x01\x00\x00')
#   [Characteristic] 00002a26-0000-1000-8000-00805f9b34fb (Handle: 16): Firmware Revision String (read), Value: bytearray(b'B.8')
#     [Descriptor] 00002904-0000-1000-8000-00805f9b34fb (Handle: 18): Characteristic Presentation Format, Value: bytearray(b'\x19\x00\x00\x00\x01\x00\x00')
#   [Characteristic] 00002a29-0000-1000-8000-00805f9b34fb (Handle: 19): Manufacturer Name String (read), Value: bytearray(b'GSH\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
#     [Descriptor] 00002904-0000-1000-8000-00805f9b34fb (Handle: 21): Characteristic Presentation Format, Value: bytearray(b'\x19\x00\x00\x00\x01\x00\x00')
#   [Characteristic] 00002a28-0000-1000-8000-00805f9b34fb (Handle: 22): Software Revision String (read), Value: bytearray(b'BLE_BF')
#     [Descriptor] 00002904-0000-1000-8000-00805f9b34fb (Handle: 24): Characteristic Presentation Format, Value: bytearray(b'\x19\x00\x00\x00\x01\x00\x00')
# [Service] 000078a2-0000-1000-8000-00805f9b34fb (Handle: 25): Vendor specific
#   [Characteristic] 00008a21-0000-1000-8000-00805f9b34fb (Handle: 26): Vendor specific (indicate)
#     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 28): Client Characteristic Configuration, Value: bytearray(b'')
#   [Characteristic] 00008a22-0000-1000-8000-00805f9b34fb (Handle: 29): Vendor specific (indicate)
#     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 31): Client Characteristic Configuration, Value: bytearray(b'')
#   [Characteristic] 00008a20-0000-1000-8000-00805f9b34fb (Handle: 32): Vendor specific (read), Value: bytearray(b'\x00\x00')
#   [Characteristic] 00008a81-0000-1000-8000-00805f9b34fb (Handle: 34): Vendor specific (write)
#   [Characteristic] 00008a82-0000-1000-8000-00805f9b34fb (Handle: 36): Vendor specific (indicate)
#     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 38): Client Characteristic Configuration, Value: bytearray(b'')%
#
# 參考：https://www.cnblogs.com/wstong2052/p/17767538.html

end_flag = False
weight = 0

def print_hex(bytes):
    l = [hex(int(i)) for i in bytes]
    return " ".join(l)

async def read_characteristic_value(address, characteristic_uuid):
    client = BleakClient(address, timeout=120)
    try:
        await client.connect()
        logging.info(f"Connected: {client.is_connected}")
        # 遍歷每個服務並獲取其特徵
        for service in client.services:
            logging.info(f"Service: {service.uuid}")
            for char in service.characteristics:
                logging.info(f"\tCharacteristic: {char.uuid}")

        def notification_handler(sender, data):
            global end_flag
            global weight
            logging.info(f"{sender}: {print_hex(data)}")
            a = data[1]
            b = data[2]
            c = data[3]
            d = data[4]
            weight = ((a + (b * 256)) + (c * (2 ** 16))) / (10 ** (256 - d))
            end_flag = True

        await client.start_notify(characteristic_uuid, notification_handler)
        logging.info('write password')
        await client.write_gatt_char('00008a81-0000-1000-8000-00805f9b34fb', bytearray([2]))

        while not end_flag:
            await asyncio.sleep(1.0)  # 監聽1秒

        await client.stop_notify(characteristic_uuid)
        logging.info(f"weight={weight}")
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )

    address = "DE387D88-BDD7-920B-49BE-B3615C8A0719" 
    characteristic_uuid = "00008a21-0000-1000-8000-00805f9b34fb"

    asyncio.run(read_characteristic_value(address, characteristic_uuid))
