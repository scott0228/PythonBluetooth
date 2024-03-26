from bleak import BleakClient
import asyncio
import struct
import logging

# 讀取 小米 溫濕度計
#　
async def read_characteristic_value(address, characteristic_uuid):
    client = BleakClient(address, timeout=120)
    try:
        await client.connect()
        # logging.info(f"Connected: {client.is_connected}")
        # 遍歷每個服務並獲取其特徵
        # for service in client.services:
        #     print(f"Service: {service.uuid}")
        #     for char in service.characteristics:
        #         print(f"Characteristic: {char.uuid}")

        MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
        model_number = await client.read_gatt_char(MODEL_NBR_UUID)

        value = await client.read_gatt_char(characteristic_uuid)
        humidity = value[2]
        voltage = struct.unpack('H', value[3:5])[0]/ 1000
        battery = round((voltage - 2.1),2) * 100
        temperature = struct.unpack('H', value[:2])[0] / 100

        logging.info(f"hygrometer,device={''.join(map(chr, model_number))} Tempterature={temperature},Humidity={humidity}i,batteryLevel={battery}")
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )

    address = "A99E3E25-FE1B-1B67-F090-613DF306A501"  # Replace with the actual address of the Bluetooth device
    characteristic_uuid = "EBE0CCC1-7A0A-4B0C-8A1A-6FF2997DA3A6"  # Replace with the UUID of the characteristic

    asyncio.run(read_characteristic_value(address, characteristic_uuid))

    # A4:C1:38:EF:5D:B6: MJWSD05MMC A99E3E25-FE1B-1B67-F090-613DF306A501
    # AdvertisementData(local_name='MJWSD05MMC', service_data={'0000fe95-0000-1000-8000-00805f9b34fb': b'\x10Y2(!\xb6]\xef8\xc1\xa4'}, rssi=-80)
    # A4:C1:38:1F:01:A6: LYWSD03MMC 6ADC354E-D6AB-880F-C007-48C0B4D14B7A
    # AdvertisementData(local_name='LYWSD03MMC', service_data={'0000fe95-0000-1000-8000-00805f9b34fb': b'0X[\x05\x01\xa6\x01\x1f8\xc1\xa4(\x01\x00'}, rssi=-71)
