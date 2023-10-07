#!/usr/bin/python3

from base_advertise import Advertisement
import bluetooth_constants
import tivo_rcu.ble_hogp
import tivo_rcu.ble_voice_service

class SharpRCUAdvertisement(Advertisement):

    DISCOVERABLE_NAME = "SHARP RCU"
    
    BASE_PATH = bluetooth_constants.BLUEZ_OBJ_ROOT + "advertisement"
    
    def __init__(self, bus, mac_address, index):
        Advertisement.__init__(self, bus, self.BASE_PATH, index, "peripheral")
        #self.add_service_uuid(tivo_rcu.ble_hogp.HIDService.SERVICE_UUID)
        #self.add_service_uuid(tivo_rcu.ble_hogp.BatteryService.SERVICE_UUID)
        self.add_service_uuid('b9524502-bb08-11ec-8422-0242ac120002')
        #self.add_service_uuid(ble_hogp.DeviceInfoService.SERVICE_UUID)
        #self.add_service_uuid(ble_voice_service.VoiceService.SERVICE_UUID)
        self.mac_address = mac_address
        self.add_local_name(self.DISCOVERABLE_NAME)
        self.add_discoverable(True)
        self.include_tx_power = True
