#!/usr/bin/python3
import dbus.service
import bluetooth_constants
import ble_hogp
import ble_voice_service

class Advertisement(dbus.service.Object):

    def __init__(self, bus, path, index, advertising_type):
        self.path = path + str(index)
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = None
        self.manufacturer_data = None
        self.solicit_uuids = None
        self.service_data = None
        self.local_name = None
        self.discoverable = False
        self.include_tx_power = None
        self.data = None
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        properties = dict()
        properties["Type"] = self.ad_type
        if self.service_uuids is not None:
            properties["ServiceUUIDs"] = dbus.Array(
                self.service_uuids, signature="s")
        if self.solicit_uuids is not None:
            properties["SolicitUUIDs"] = dbus.Array(
                self.solicit_uuids, signature="s")
        if self.manufacturer_data is not None:
            properties["ManufacturerData"] = dbus.Dictionary(
                self.manufacturer_data, signature="qv"
            )
        if self.service_data is not None:
            properties["ServiceData"] = dbus.Dictionary(
                self.service_data, signature="sv"
            )
        if self.local_name is not None:
            properties["LocalName"] = dbus.String(self.local_name)
        if self.discoverable is not None:
            properties['Discoverable'] = dbus.Boolean(self.discoverable)
        if self.include_tx_power is not None:
            properties["IncludeTxPower"] = dbus.Boolean(self.include_tx_power)

        if self.data is not None:
            properties["Data"] = dbus.Dictionary(self.data, signature="yv")
        return {bluetooth_constants.ADVERTISEMENT_INTERFACE: properties}

    def get_path(self):
        return dbus.ObjectPath(self.path)
    
    def get_local_name(self):
        return self.local_name

    def get_advertisement_info(self):
        advertisement_info = "{} [{}]".format(
            bluetooth_constants.DISCOVERABLE_NAME_BASE, self.mac_address)
        return advertisement_info

    def add_service_uuid(self, uuid):
        if not self.service_uuids:
            self.service_uuids = []
        self.service_uuids.append(uuid)

    def add_solicit_uuid(self, uuid):
        if not self.solicit_uuids:
            self.solicit_uuids = []
        self.solicit_uuids.append(uuid)

    def add_manufacturer_data(self, manuf_code, data):
        if not self.manufacturer_data:
            self.manufacturer_data = dbus.Dictionary({}, signature="qv")
        self.manufacturer_data[manuf_code] = dbus.Array(data, signature="y")

    def add_service_data(self, uuid, data):
        if not self.service_data:
            self.service_data = dbus.Dictionary({}, signature="sv")
        self.service_data[uuid] = dbus.Array(data, signature="y")

    def add_local_name(self, name):
        if not self.local_name:
            self.local_name = ""
        self.local_name = dbus.String(name)

    def add_discoverable(self, discoverable):
        self.discoverable = discoverable

    def add_data(self, ad_type, data):
        if not self.data:
            self.data = dbus.Dictionary({}, signature="yv")
        self.data[ad_type] = dbus.Array(data, signature="y")

    @dbus.service.method(bluetooth_constants.DBUS_PROPERTIES, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != bluetooth_constants.ADVERTISEMENT_INTERFACE:
            raise bluetooth_exceptions.InvalidArgsException()
        return self.get_properties()[bluetooth_constants.ADVERTISEMENT_INTERFACE]

    @dbus.service.method(bluetooth_constants.ADVERTISEMENT_INTERFACE, in_signature="", out_signature="")
    def Release(self):
        print("%s: Released!" % self.path)

class RCUAdvertisement(Advertisement):
    
    BASE_PATH = bluetooth_constants.BLUEZ_OBJ_ROOT + "advertisement"
    def __init__(self, bus, mac_address, index):
        Advertisement.__init__(self, bus, self.BASE_PATH, index, "peripheral")
        #self.add_service_uuid(ble_hogp.HIDService.SERVICE_UUID)
        #self.add_service_uuid(ble_hogp.BatteryService.SERVICE_UUID)
        #self.add_service_uuid(ble_hogp.DeviceInfoService.SERVICE_UUID)
        self.add_service_uuid(ble_voice_service.VoiceService.SERVICE_UUID)
        self.add_manufacturer_data(
            0xFFFF, [0x70, 0x74],
        )
        self.mac_address = mac_address
        self.add_local_name(bluetooth_constants.DISCOVERABLE_NAME_BASE)
        self.add_discoverable(True)
        self.include_tx_power = True
