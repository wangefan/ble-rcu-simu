#!/usr/bin/python3
import bluetooth_constants
import dbus.mainloop.glib
from gi.repository import GLib
import dbus
import dbus.exceptions
import dbus.service
from advertise import RCUAdvertisement
from agent import Agent
from ble_hogp import DeviceInfoService, BatteryService, HIDService
from key_event_monitor import KeyEventMonitor
from enum import Enum


class MainState(Enum):
    ADVERTISING = 0
    CONNECTING = 1
    CONNECTED = 2

g_mainloop = None
g_main_state = MainState.ADVERTISING
g_ad_manager = None 
g_rcu_advertisement = None
g_application = None



def register_ad_cb():
    print(f"{g_rcu_advertisement.get_local_name()} start advertising.. (press q to exit")

def register_ad_error_cb(error):
    if "AlreadyExists" in str(error):
        print(f"{g_rcu_advertisement.get_local_name()} has already registered, keep advertising.. (press q to exit")
    else:
        print(f"Failed to register RCUAdvertisement: {str(error)}, exit!")
        closeAll()


def application_all_services_registered_cb(path):
    print(f"application_all_services_registered_cb called, path = {path}")
    update_state(path)

class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """

    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.all_services_registered = False
        self.all_services_registered_cb = None
        self.hid_service = HIDService(bus, self.service_registered_cb)
        self.add_service(self.hid_service)
        self.add_service(DeviceInfoService(bus))
        self.add_service(BatteryService(bus))

        self.online = False
        self.KeyEventMonitor = KeyEventMonitor(self.onKeyEvent, self.onExit)
        self.KeyEventMonitor.start()

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def service_registered_cb(self, obj_path):
        print(f"Application.service_registered_cb get {obj_path}")
        self.all_services_registered = True
        if self.all_services_registered_cb != None:
            self.all_services_registered_cb(obj_path)

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

    def set_online(self, online):
        self.online = online

    def get_all_services_registered(self):
        return self.all_services_registered
    
    def set_all_services_unregistered(self):
        self.all_services_registered = False
    
    def set_all_services_registered_cb(self, cb):
        print(f"Application.set_all_services_registered_cb called")
        self.all_services_registered_cb = cb

    def onExit(self):
        closeAll()

    def onKeyEvent(self, key_event):
        if self.online:
            self.hid_service.onKeyEvent(key_event)
        else:
            pass

def register_app_cb():
    print('4. Registered GATT application ok')


def register_app_error_cb(error):
    print('4. Failed to register GATT application: ' + str(error))
    closeAll()


def update_state(path):
    bus = dbus.SystemBus()
    properties_in_path = dbus.Interface(bus.get_object(
        bluetooth_constants.BLUEZ_SERVICE_NAME, path), bluetooth_constants.DBUS_PROPERTIES)
    connected_state = properties_in_path.Get(
        bluetooth_constants.DEVICE_INTERFACE, bluetooth_constants.DEVICE_PROP_CONNECTED)
    print(f"update_state, path = {path}, connected_state = {connected_state}")

    global g_application
    if connected_state == True:
        if g_application.get_all_services_registered():
            g_main_state = MainState.CONNECTED
        else:
            g_main_state = MainState.CONNECTING
    else:
        g_main_state = MainState.ADVERTISING

    if g_main_state == MainState.ADVERTISING:
        g_application.set_online(False)
        print("Application is not ready, into advertising state")
        start_advertising()
    elif g_main_state == MainState.CONNECTING:
        g_application.set_online(False)
        stop_advertising()
        print("Now is connecting ...")
    elif g_main_state == MainState.CONNECTED:
        stop_advertising()
        g_application.set_online(True)
        print(
            "Application is ready, press any key to send the events.. (press q to exit")
        

"""
When a connection for a device which is already known is established, a PropertiesChanged signal is
instead emitted with the Connected property
"""
def properties_changed(interface, changed, invalidated, path):
    if (interface == bluetooth_constants.DEVICE_INTERFACE):
        print(f"properties_changed called, path = {path}")
        if ("Connected" in changed):
            if ["changed" == 0]: # mean from connected to disconnected, we need to reset services to unregistered
                g_application.set_all_services_unregistered()
            update_state(path)

"""
When a connection for a previously unknown device is established, an InterfacesAdded signal is
emitted by a device object with Connected status.
"""
def interfaces_added(path, interfaces):
    if bluetooth_constants.DEVICE_INTERFACE in interfaces:
        print(f"interfaces_added called, path = {path}")
        properties = interfaces[bluetooth_constants.DEVICE_INTERFACE]
        if ("Connected" in properties):
            update_state(path)

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
    try:
        g_ad_manager.UnregisterAdvertisement(g_rcu_advertisement.get_path())
    except:
        dbus.exceptions.DBusException
        pass
    print(f"{g_rcu_advertisement.get_local_name()} stop advertising")
        

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
    adapter_props.Set(bluetooth_constants.ADAPTER_INTERFACE,
                      bluetooth_constants.ADAPTER_PROP_DISCOVERABLE, dbus.Boolean(1))
    adapter_props.Set(bluetooth_constants.ADAPTER_INTERFACE,
                      bluetooth_constants.ADAPTER_PROP_PAIRABLE, dbus.Boolean(1))
    mac_address = adapter_props.Get(
        bluetooth_constants.ADAPTER_INTERFACE, bluetooth_constants.ADAPTER_PROP_MAC_ADDRESS)

    print("2. Agent procedure")
    AGENT_PATH = bluetooth_constants.BLUEZ_OBJ_ROOT + "agent"
    agent = Agent(bus, AGENT_PATH)
    agent_manager = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, '/org/bluez'),
                                   bluetooth_constants.AGENT_MANAGER_INTERFACE)
    agent_manager.RegisterAgent(AGENT_PATH, "NoInputNoOutput")
    agent_manager.RequestDefaultAgent(AGENT_PATH)

    print("3. Advertise procedure")
    global g_ad_manager
    g_ad_manager = dbus.Interface(bus.get_object(
        bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_obj), bluetooth_constants.ADVERTISING_MANAGER_INTERFACE)
    global g_rcu_advertisement
    g_rcu_advertisement = RCUAdvertisement(bus, mac_address, 0)
    start_advertising()

    print('4. Registering GATT procedure')
    gatt_service_manager = dbus.Interface(
        bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_obj),
        bluetooth_constants.GATT_MANAGER_INTERFACE)

    global g_application
    g_application = Application(bus)
    g_application.set_all_services_registered_cb(application_all_services_registered_cb)
    gatt_service_manager.RegisterApplication(g_application.get_path(), {},
                                             reply_handler=register_app_cb,
                                             error_handler=register_app_error_cb)

    global g_mainloop
    g_mainloop = GLib.MainLoop()
    g_mainloop.run()
    print('5. Process end')


if __name__ == "__main__":
    main()
