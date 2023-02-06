#!/usr/bin/python3
import bluetooth_exceptions
import bluetooth_constants
import dbus.mainloop.glib
from gi.repository import GLib
import dbus
import dbus.exceptions
import dbus.service
from Advertise import RCUAdvertisement

g_mainloop = None
g_ad_manager = None 
g_rcu_advertisement = None


def register_ad_cb():
    print("Registered RCUAdvertisement " + g_rcu_advertisement.get_path() + ", instruct controller to start advertising", )


def register_ad_error_cb(error):
    print("2. Failed to register RCUAdvertisement: " + str(error))
    g_mainloop.quit()

class Descriptor(dbus.service.Object):
    """
    org.bluez.GattDescriptor1 interface implementation
    """
    def __init__(self, bus, index, uuid, flags, characteristic):
        self.path = characteristic.path + '/desc' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.chrc = characteristic
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                bluetooth_constants.GATT_DESCRIPTOR_INTERFACE: {
                        'Characteristic': self.chrc.get_path(),
                        'UUID': self.uuid,
                        'Flags': self.flags,
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(bluetooth_constants.DBUS_PROPERTIES,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != bluetooth_constants.GATT_DESCRIPTOR_INTERFACE:
            raise bluetooth_exceptions.InvalidArgsException()

        return self.get_properties()[bluetooth_constants.GATT_DESCRIPTOR_INTERFACE]

    @dbus.service.method(bluetooth_constants.GATT_DESCRIPTOR_INTERFACE,
                        in_signature='a{sv}',
                        out_signature='ay')
    def ReadValue(self, options):
        print ('Default ReadValue called, returning error')
        raise bluetooth_exceptions.NotSupportedException()

    @dbus.service.method(bluetooth_constants.GATT_DESCRIPTOR_INTERFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print('Default WriteValue called, returning error')
        raise bluetooth_exceptions.NotSupportedException()
class Characteristic(dbus.service.Object):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE: {
                        'Service': self.service.get_path(),
                        'UUID': self.uuid,
                        'Flags': self.flags,
                        'Descriptors': dbus.Array(
                                self.get_descriptor_paths(),
                                signature='o')
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptor_paths(self):
        result = []
        for desc in self.descriptors:
            result.append(desc.get_path())
        return result

    def get_descriptors(self):
        return self.descriptors

    @dbus.service.method(bluetooth_constants.DBUS_PROPERTIES,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE:
            raise bluetooth_exceptions.InvalidArgsException()

        return self.get_properties()[bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE]

    @dbus.service.method(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        print('Default ReadValue called, returning error')
        raise bluetooth_exceptions.NotSupportedException()

    @dbus.service.method(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print('Default WriteValue called, returning error')
        raise bluetooth_exceptions.NotSupportedException()

    @dbus.service.method(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE)
    def StartNotify(self):
        print('Default StartNotify called, returning error')
        raise bluetooth_exceptions.NotSupportedException()

    @dbus.service.method(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE)
    def StopNotify(self):
        print('Default StopNotify called, returning error')
        raise bluetooth_exceptions.NotSupportedException()

    @dbus.service.signal(bluetooth_constants.DBUS_PROPERTIES, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass
        
    @dbus.service.signal(bluetooth_constants.DBUS_PROPERTIES, signature='ay')
    def ReportValueChanged(self, reportValue):
        pass

class Service(dbus.service.Object):
    """
    org.bluez.GattService1 interface implementation
    """

    # The constructor also requires a DBus bus object, a UUID with which GATT clients can identify
    # the type of GATT service represented and an indicator of whether it is a primary or
    # secondary service.
    def __init__(self, bus, path_base, uuid, primary):
        self.path = path_base
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            bluetooth_constants.GATT_SERVICE_INTERFACE: {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': dbus.Array(
                    self.get_characteristic_paths(),
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristic_paths(self):
        result = []
        for chrc in self.characteristics:
            result.append(chrc.get_path())
        return result

    def get_characteristics(self):
        return self.characteristics

    @dbus.service.method(bluetooth_constants.DBUS_PROPERTIES,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != bluetooth_constants.GATT_SERVICE_INTERFACE:
            raise bluetooth_exceptions.InvalidArgsException()
        return self.get_properties()[bluetooth_constants.GATT_SERVICE_INTERFACE]

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

class RCUService(Service):
    """
    RCU service that provides characteristics and descriptors that
    exercise various API functionality.
    """
    RCU_PATH_BASE = "/org/bluez/rcu/gatt_service"
    RCU_SVC_UUID = '12345678-1234-5678-1234-56789abcdef0'

    def __init__(self, bus):
        Service.__init__(self, bus, self.RCU_PATH_BASE, self.RCU_SVC_UUID, True)


class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """

    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.add_service(BatteryService(bus))
        self.add_service(DeviceInfoService(bus))

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    # The Object Manager interface method GetManagedObjects is exported. This makes the
    # method available to be called by other DBus applications, in our case the BlueZ bluetooth
    # daemon and this is how it determines the list of services, characteristics and descriptors
    # implemented by our application and results in DBus objects for each being registered on the
    # system bus.
    @dbus.service.method(bluetooth_constants.DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}

        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()

        return response


def register_app_cb():
    print('Registered GATT application')


def register_app_error_cb(error):
    print('Failed to register GATT application: ' + str(error))
    g_mainloop.quit()

def set_connected_status(status):
    if (status == 1):
        print("connected")
        stop_advertising()
    else:
        print("disconnected")
        start_advertising()

"""
When a connection for a device which is already known is established, a PropertiesChanged signal is
instead emitted with the Connected property
"""
def properties_changed(interface, changed, invalidated, path):
    if (interface == bluetooth_constants.DEVICE_INTERFACE):
        if ("Connected" in changed):
            set_connected_status(changed["Connected"])

"""
When a connection for a previously unknown device is established, an InterfacesAdded signal is
emitted by a device object with Connected status.
"""
def interfaces_added(path, interfaces):
    if bluetooth_constants.DEVICE_INTERFACE in interfaces:
        properties = interfaces[bluetooth_constants.DEVICE_INTERFACE]
        if ("Connected" in properties):
            set_connected_status(properties["Connected"])

"""
Returns the first object that the bluez service has that has a GattManager1 interface,
which is suppose to be the bluetooth adapter 'org/bluez/hci0'.
"""
def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, '/'),
                               bluetooth_constants.DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if bluetooth_constants.GATT_MANAGER_INTERFACE in props.keys():
            return o

    return None


def start_advertising():
    global g_ad_manager 
    global g_rcu_advertisement
    # This causes BlueZ to instruct the controller to start advertising
    g_ad_manager.RegisterAdvertisement(
        g_rcu_advertisement.get_path(),
        {},
        reply_handler=register_ad_cb,
        error_handler=register_ad_error_cb,
    )

def stop_advertising():
    global g_ad_manager 
    global g_rcu_advertisement
    g_ad_manager.UnregisterAdvertisement(g_rcu_advertisement.get_path())
    print("Unregistered RCUAdvertisement " + g_rcu_advertisement.get_path() + ", instruct controller to stop advertising")

def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    # handle connections status
    bus.add_signal_receiver(properties_changed,
    dbus_interface = bluetooth_constants.DBUS_PROPERTIES,
    signal_name = "PropertiesChanged",
    path_keyword = "path")

    bus.add_signal_receiver(interfaces_added,
    dbus_interface = bluetooth_constants.DBUS_OM_IFACE,
    signal_name = "InterfacesAdded")

    # require bluetooth adapter
    adapter_obj = find_adapter(bus)
    if not adapter_obj:
        print('adapter_obj not found')
        return

    print("1. Power on the bluetooth adapter..")
    adapter_props = dbus.Interface(bus.get_object(
        bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_obj), bluetooth_constants.DBUS_PROPERTIES)
    adapter_props.Set(bluetooth_constants.ADAPTER_INTERFACE,
                      bluetooth_constants.ADAPTER_PROP_POWER, dbus.Boolean(1))

    print("2. Advertise procedure")
    global g_ad_manager
    g_ad_manager = dbus.Interface(bus.get_object(
        bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_obj), bluetooth_constants.ADVERTISING_MANAGER_INTERFACE)
    global g_rcu_advertisement
    g_rcu_advertisement = RCUAdvertisement(bus, 0)
    start_advertising()

    print('3. Registering GATT procedure')
    gatt_service_manager = dbus.Interface(
        bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_obj),
        bluetooth_constants.GATT_MANAGER_INTERFACE)

    app = Application(bus)
    gatt_service_manager.RegisterApplication(app.get_path(), {},
                                             reply_handler=register_app_cb,
                                             error_handler=register_app_error_cb)

    global g_mainloop
    g_mainloop = GLib.MainLoop()
    g_mainloop.run()


if __name__ == "__main__":
    main()
