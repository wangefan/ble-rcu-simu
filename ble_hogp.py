#!/usr/bin/python3
import dbus.service
import bluetooth_constants
from gi.repository import GLib
from ble_base import Descriptor, Characteristic, Service

class BatteryLevelCharacteristic(Characteristic):
    """
    Fake Battery Level characteristic. The battery level is drained by 2 points
    every 5 seconds.

    """
    BATTERY_LVL_UUID = '2a19'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.BATTERY_LVL_UUID,
                ['read', 'notify'],
                service)
        self.notifying = False
        self.notifyCnt = 0
        self.battery_lvl = 100
        #self.timer = GObject.timeout_add(60000, self.drain_battery)

    def notify_battery_level(self):
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, { 'Value': [dbus.Byte(self.battery_lvl)] }, [])
        self.notifyCnt += 1
        
    def drain_battery(self):
        if not self.notifying: return True
        if(self.notifyCnt > 2): return False #Update battery level 3 times then stop
        
        if self.battery_lvl > 0:
            self.battery_lvl -= 2
            if self.battery_lvl < 5:
                #self.battery_lvl = 0
                GLib.source_remove(self.timer)
                
        print('Battery Level drained: ' + repr(self.battery_lvl))
        self.notify_battery_level()
        return True
 
    def ReadValue(self, options):
        print('Battery Level read: ' + repr(self.battery_lvl))
        return [dbus.Byte(self.battery_lvl)]

    def StartNotify(self):
        print('Start Battery Notify')
        
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True
        print('Battery Notify 1')
        self.timer = GLib.timeout_add(2000, self.drain_battery)
        print('Battery Notify emd')

    def StopNotify(self):
        print('Stop Battery Notify')
        
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False
class BatteryService(Service):
    """
    Fake Battery service that emulates a draining battery.

    """
    PATH_BASE = "/org/bluez/rcu/batt_service"
    SERVICE_UUID = '180f'

    def __init__(self, bus):
        Service.__init__(self, bus, self.PATH_BASE, self.SERVICE_UUID, True)
        self.add_characteristic(BatteryLevelCharacteristic(bus, 0, self))

"""
The Manufacturer Name String characteristic shall represent the name of the
manufacturer of the device.

Characteristic Behavior:
The Manufacturer Name String characteristic returns its value when read using the
GATT Characteristic Value Read procedure.
"""
class ManufacturerNameCharacteristic(Characteristic):
    CHARACTERISTIC_UUID = '2A29'
    MANUFACTURER_NAME = 'Fake RCU Manufacturer Name'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.CHARACTERISTIC_UUID,
                ["read"],
                service)
        self.value = dbus.Array(self.MANUFACTURER_NAME.encode(), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read RCU Manufacturer Name : {self.value}')
        return self.value

"""
The Model Number String characteristic shall represent the model number that is
assigned by the device vendor.

Characteristic Behavior:
The Model Number String characteristic returns its value when read using the GATT
Characteristic Value Read procedure.
"""
class ModelNumberCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A24'
    MODEL_NUMBER = 'FAKE_RCU_01'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.CHARACTERISTIC_UUID,
                ["read"],
                service)
        self.value = dbus.Array(self.MODEL_NUMBER.encode(), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read ModelNumberCharacteristic: {self.value}')
        return self.value

"""
The Software Revision String characteristic shall represent the software revision for the
software within the device.

Characteristic Behavior:
The Software Revision String characteristic returns its value when read using the GATT
Characteristic Value Read procedure.
"""
class VersionCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A28'
    VERSION_NUMBER = '1.0.0'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.CHARACTERISTIC_UUID,
                ["read"],
                service)
        
        self.value = dbus.Array(self.VERSION_NUMBER.encode(), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read VersionCharacteristic: {self.value}')
        return self.value

class DeviceInfoService(Service):

    SERVICE_UUID = '180A'
    PATH_BASE = "/org/bluez/rcu/device_info_service"

    def __init__(self, bus):
        Service.__init__(self, bus, self.PATH_BASE, self.SERVICE_UUID, True)
        self.add_characteristic(ManufacturerNameCharacteristic(bus, 0, self))
        self.add_characteristic(ModelNumberCharacteristic(bus, 1, self))
        self.add_characteristic(VersionCharacteristic(bus, 2, self))