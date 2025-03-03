#!/usr/bin/python3

from base_advertise import Advertisement
import bluetooth_constants
import tivo_rcu.ble_hogp
import tivo_rcu.ble_voice_service

class TiVoS4KRCUAdvertisement(Advertisement):

    DISCOVERABLE_NAME = "TiVo Remote"
    
    BASE_PATH = bluetooth_constants.BLUEZ_OBJ_ROOT + "advertisement"

    def make_manufacturer_data(self):
        manufacturer_id = 0x21
        version_code = 1
        device_name= "tivo_remote"
        manufacturer_data_string = f"{device_name}_{version_code}"
        return manufacturer_id, bytes(manufacturer_data_string, "utf-8")
    
    def __init__(self, bus, mac_address, index):
        Advertisement.__init__(self, bus, self.BASE_PATH, index, "peripheral")
        self.add_service_uuid(tivo_rcu.ble_hogp.HIDService.SERVICE_UUID)
        self.add_service_uuid(tivo_rcu.ble_hogp.BatteryService.SERVICE_UUID)
        #self.add_service_uuid(ble_hogp.DeviceInfoService.SERVICE_UUID)
        #self.add_service_uuid(ble_voice_service.VoiceService.SERVICE_UUID)
        id, data = self.make_manufacturer_data()
        self.add_manufacturer_data(id, data)
        self.mac_address = mac_address
        self.add_local_name(self.DISCOVERABLE_NAME)
        self.add_discoverable(True)
        self.include_tx_power = True
