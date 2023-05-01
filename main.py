#!/usr/bin/python3
from ble_voice_service import VoiceService
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
from PyQt5 import QtCore, QtWidgets
from key_event_name import KEY_EVENT_NAME_VOICE
from tivo_rcu import TivoRcuDlg
import argparse

class MainState(Enum):
    ADVERTISING = 0
    CONNECTING = 1
    CONNECTED = 2


g_core_application = None
g_main_state = MainState.ADVERTISING
g_ad_manager = None
g_rcu_advertisement = None
g_tivo_rcu_service = None


def register_ad_cb():
    print(f"{g_rcu_advertisement.get_advertisement_info()} start advertising.. (press esc to exit")

def register_ad_error_cb(error):
    if "AlreadyExists" in str(error):
        print(f"{g_rcu_advertisement.get_advertisement_info()} has already registered, keep advertising.. (press esc to exit")
    else:
        print(f"Failed to register RCUAdvertisement: {str(error)}, exit!")
        closeAll()


def application_all_services_registered_cb(path):
    print(f"application_all_services_registered_cb called, path = {path}")
    update_state(path)

class TivoRCUService(dbus.service.Object):
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
        self.voice_service = VoiceService(bus)
        self.add_service(self.hid_service)
        self.add_service(self.voice_service)
        self.add_service(DeviceInfoService(bus))
        self.add_service(BatteryService(bus))

        self.tivo_ruc_dlg = TivoRcuDlg(self.onKeyEvent, self.onCaptureKeyboard)

        self.online = False
        self.KeyEventMonitor = KeyEventMonitor(self.onKeyEvent, self.onExit)
        self.KeyEventMonitor.start()

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def service_registered_cb(self, obj_path):
        print(f"TivoRCUService.service_registered_cb get {obj_path}")
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
        if self.online == True:
            self.tivo_ruc_dlg.show()
        else:
            self.tivo_ruc_dlg.hide()

    def get_all_services_registered(self):
        return self.all_services_registered
    
    def set_all_services_unregistered(self):
        self.all_services_registered = False
    
    def set_all_services_registered_cb(self, cb):
        print(f"TivoRCUService.set_all_services_registered_cb called")
        self.all_services_registered_cb = cb

    def onExit(self):
        closeAll()

    def onKeyEvent(self, key_event_name):
        if self.online:
            self.hid_service.onKeyEvent(key_event_name)
            if KEY_EVENT_NAME_VOICE == key_event_name:
                self.voice_service.VoiceSearch()
        else:
            pass

    def onCaptureKeyboard(self, b_capture):
        self.KeyEventMonitor.setCaptureKeyboard(b_capture)


def register_app_cb():
    print('4. Registered GATT application ok')


def register_app_error_cb(error):
    print('4. Failed to register GATT application: ' + str(error))
    closeAll()


# If the object path by central has the property "Connected" with True, 
# It experiences central is connected with peripheral but not workable 
# since the profiles have no registered yet, hence it would be the state 
# MainState.CONNECTING.
def update_state(path):
    connected_state = False
    bus = dbus.SystemBus()
    try:
        properties_in_path = dbus.Interface(bus.get_object(
            bluetooth_constants.BLUEZ_SERVICE_NAME, path), bluetooth_constants.DBUS_PROPERTIES)
        connected_state = properties_in_path.Get(
            bluetooth_constants.DEVICE_INTERFACE, bluetooth_constants.DEVICE_PROP_CONNECTED)
    except Exception as e:
        print(f"update_state, exception occurs with :{e}")    
        
    print(f"update_state, path = {path}, connected_state = {connected_state}")

    global g_tivo_rcu_service
    if connected_state == True:
        if g_tivo_rcu_service.get_all_services_registered():
            g_main_state = MainState.CONNECTED
        else:
            g_main_state = MainState.CONNECTING
    else:
        g_main_state = MainState.ADVERTISING

    if g_main_state == MainState.ADVERTISING:
        g_tivo_rcu_service.set_online(False)
        print("TivoRCUService is not ready, into advertising state")
        start_advertising()
    elif g_main_state == MainState.CONNECTING:
        g_tivo_rcu_service.set_online(False)
        stop_advertising()
        print("Now is connecting ...")
    elif g_main_state == MainState.CONNECTED:
        stop_advertising()
        g_tivo_rcu_service.set_online(True)
        print(
            "TivoRCUService is ready, press any key to send the events.. (press esc to exit")
        

"""
When a connection for a device which is already known is established, a PropertiesChanged signal is
instead emitted with the Connected property
"""
def properties_changed(interface, changed, invalidated, path):
    if (interface == bluetooth_constants.DEVICE_INTERFACE):
        if ("Connected" in changed):
            print(f"properties_changed called with Connected property, path = {path}")
            if changed["Connected"] == 0: # mean from connected to disconnected, we need to reset services to unregistered
                print("call g_tivo_rcu_service.set_all_services_unregistered()")
                g_tivo_rcu_service.set_all_services_unregistered()
            update_state(path)

"""
When a connection for a previously unknown device is established, an InterfacesAdded signal is
emitted by a device object with Connected status.
"""
def interfaces_added(path, interfaces):
    if bluetooth_constants.DEVICE_INTERFACE in interfaces:
        properties = interfaces[bluetooth_constants.DEVICE_INTERFACE]
        if ("Connected" in properties):
            print(f"interfaces_added called with Connected property, path = {path}")
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
    print(f"{g_rcu_advertisement.get_advertisement_info()} stop advertising")
        

def closeAll():
    stop_advertising()
    global g_core_application
    if g_core_application != None:
        g_core_application.quit()

def main():
    parser = argparse.ArgumentParser(description='RCU tool parameters')
    parser.add_argument('-io', dest='io_capability_type', nargs='?', type=int,
                        help='Specify the IO capability of the device, 0: NoInputNoOutput, 1: DisplayYesNo, 2: KeyboardDisplay, 3: DisplayOnly, 4:  KeyboardOnly')
    args = parser.parse_args()

    io_capability_type = args.io_capability_type
    io_capability = "NoInputNoOutput"
    if io_capability_type == 1:
        io_capability = "DisplayYesNo"
    elif io_capability_type == 2:
        io_capability = "KeyboardDisplay"
    elif io_capability_type == 3:
        io_capability = "DisplayOnly"
    elif io_capability_type == 4:
        io_capability = "KeyboardOnly"

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
    adapter_props.Set(bluetooth_constants.ADAPTER_INTERFACE,
                      bluetooth_constants.ADAPTER_PROP_ALIAS, dbus.String(
                          bluetooth_constants.DISCOVERABLE_NAME_BASE))
    mac_address = adapter_props.Get(
        bluetooth_constants.ADAPTER_INTERFACE, bluetooth_constants.ADAPTER_PROP_MAC_ADDRESS)

    print(f"2. Agent procedure, register with io: {io_capability}")
    AGENT_PATH = bluetooth_constants.BLUEZ_OBJ_ROOT + "agent"
    agent = Agent(bus, AGENT_PATH)
    agent_manager = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, '/org/bluez'),
                                   bluetooth_constants.AGENT_MANAGER_INTERFACE)
    agent_manager.RegisterAgent(AGENT_PATH, io_capability)
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

    global g_core_application
    g_core_application = QtWidgets.QApplication([])

    global g_tivo_rcu_service
    g_tivo_rcu_service = TivoRCUService(bus)
    g_tivo_rcu_service.set_all_services_registered_cb(application_all_services_registered_cb)
    gatt_service_manager.RegisterApplication(g_tivo_rcu_service.get_path(), {},
                                             reply_handler=register_app_cb,
                                             error_handler=register_app_error_cb)

    g_core_application.exec_()
    print('5. Process end')


if __name__ == "__main__":
    main()
