#!/usr/bin/python3
import bluetooth_constants
import dbus.mainloop.glib
from gi.repository import GLib
import dbus
import dbus.exceptions
import dbus.service
from Advertise import RCUAdvertisement
from agent import Agent
from ble_hogp import DeviceInfoService, BatteryService, HIDService
from key_event_monitor import KeyEventMonitor

g_mainloop = None
g_is_advertising = False
g_ad_manager = None 
g_rcu_advertisement = None
g_application = None


def register_ad_cb():
    g_is_advertising = True
    print("Registered RCUAdvertisement " + g_rcu_advertisement.get_path() + ", instruct controller to start advertising.. (press q to exit process)", )

def register_ad_error_cb(error):
    g_is_advertising = False
    print("Failed to register RCUAdvertisement: " + str(error))
    closeAll()

"""
class RCUService(Service):
    
    RCU service that provides characteristics and descriptors that
    exercise various API functionality.
    
    RCU_PATH_BASE = "/org/bluez/rcu/gatt_service"
    RCU_SVC_UUID = '12345678-1234-5678-1234-56789abcdef0'

    def __init__(self, bus):
        Service.__init__(self, bus, self.RCU_PATH_BASE, self.RCU_SVC_UUID, True)
"""

class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """

    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.hid_service = HIDService(bus)
        self.add_service(self.hid_service)
        self.add_service(DeviceInfoService(bus))
        self.add_service(BatteryService(bus))

        self.connected = False
        self.KeyEventMonitor = KeyEventMonitor(self.onKeyEvent, self.onExit)
        self.KeyEventMonitor.start()

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

    def set_connected(self, connected):
        self.connected = connected

    def onExit(self):
        closeAll()

    def onKeyEvent(self, key_event):
        if self.connected:
            print(
                f'\rApplication.onKeyEvent(key_event): key_event = {key_event}\r')
            self.hid_service.onKeyEvent(key_event)
        else:
            pass

def register_app_cb():
    print('4. Registered GATT application ok')


def register_app_error_cb(error):
    print('4. Failed to register GATT application: ' + str(error))
    closeAll()

def set_connected_status(status):
    global g_application
    if (status == 1):
        g_application.set_connected(True)
        print("connected")
        stop_advertising()
    else:
        g_application.set_connected(False)
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
    if g_is_advertising == False:
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
    if g_is_advertising:
        g_ad_manager.UnregisterAdvertisement(g_rcu_advertisement.get_path())
        print("Unregistered RCUAdvertisement " + g_rcu_advertisement.get_path() + ", instruct controller to stop advertising")

def closeAll():
    stop_advertising()
    global g_mainloop
    if g_mainloop != None:
        g_mainloop.quit()

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

    print("2. Agent procedure")
    AGENT_PATH = bluetooth_constants.BLUEZ_OBJ_ROOT + "agent"
    agent = Agent(bus, AGENT_PATH)
    agent_manager = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, '/org/bluez'),
                                   bluetooth_constants.AGENT_MANAGER_INTERFACE)
    agent_manager.RegisterAgent(AGENT_PATH, "NoInputNoOutput")

    print("3. Advertise procedure")
    global g_ad_manager
    g_ad_manager = dbus.Interface(bus.get_object(
        bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_obj), bluetooth_constants.ADVERTISING_MANAGER_INTERFACE)
    global g_rcu_advertisement
    g_rcu_advertisement = RCUAdvertisement(bus, 0)
    start_advertising()

    print('4. Registering GATT procedure')
    gatt_service_manager = dbus.Interface(
        bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_obj),
        bluetooth_constants.GATT_MANAGER_INTERFACE)

    global g_application
    g_application = Application(bus)
    gatt_service_manager.RegisterApplication(g_application.get_path(), {},
                                             reply_handler=register_app_cb,
                                             error_handler=register_app_error_cb)

    global g_mainloop
    g_mainloop = GLib.MainLoop()
    g_mainloop.run()
    print('5. Process end')


if __name__ == "__main__":
    main()
