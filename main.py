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
import bluetooth_utils


g_core_application = None
g_ad_manager = None
g_gatt_service_manager = None
g_rcu_advertisement = None
g_tivo_rcu_service = None
# {obj path: {"Paired": True/False, "Connected": True/False, "ServiceResolved": True/False},
g_tivo_tv_dict = {}
#  obj path2: {"Paired": True/False, "Connected": True/False, "ServiceResolved": True/False}, ...}
# ex: {"/org/bluez/hci0/dev_00_11_22_33_44_55": {"Paired": False, "Connected": False, "ServiceResolved": False},
#      "/org/bluez/hci0/dev_00_11_22_33_44_56": {"Paired": True, "Connected": True, "ServiceResolved": True}}


def register_ad_cb():
    print(
        f"{g_rcu_advertisement.get_advertisement_info()} start advertising.. (press esc to exit")


def register_ad_error_cb(error):
    if "AlreadyExists" in str(error):
        print(
            f"{g_rcu_advertisement.get_advertisement_info()} has already registered, keep advertising.. (press esc to exit")
    else:
        print(f"Failed to register RCUAdvertisement: {str(error)}, exit!")
        closeAll()


class TivoRCUService(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """

    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.hid_service = HIDService(bus)
        self.add_service(self.hid_service)

        # Prepare voice service
        self.tivo_ruc_dlg = TivoRcuDlg(self.onKeyEvent, self.onCaptureKeyboard)
        self.voice_service = VoiceService(bus, self.tivo_ruc_dlg)
        self.add_service(self.voice_service)
        self.add_service(DeviceInfoService(bus))
        self.add_service(BatteryService(bus))

        self.connected_device_path = None
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

    def set_connected_device(self, device_path):
        self.connected_device_path = device_path
        if self.connected_device_path != None:
            self.tivo_ruc_dlg.show()
        else:
            self.tivo_ruc_dlg.hide()

    def get_connected_device(self):
        return self.connected_device_path

    def onExit(self):
        print(f"onExit begin")
        connected_device = self.get_connected_device()
        # if there is connection exist, disconnect it
        if connected_device != None:
            device_interface = bluetooth_utils.get_object_interface(
                connected_device, bluetooth_constants.DEVICE_INTERFACE)
            device_interface.Disconnect()
            print(f"onExit, disconnect {connected_device} end")
        closeAll()

    def onKeyEvent(self, key_event_name):
        if self.connected_device_path:
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


def update_state(path):
    global g_tivo_tv_dict
    tv_status = g_tivo_tv_dict.get(path, None)
    if tv_status is None:
        tv_status = {bluetooth_constants.DEVICE_PROP_PAIRED: None,
                     bluetooth_constants.DEVICE_PROP_CONNECTED: None,
                     bluetooth_constants.DEVICE_PROP_SERVICES_RESOLVED: None}
        g_tivo_tv_dict[path] = tv_status

    paired = bluetooth_utils.get_device_property(
        path, bluetooth_constants.DEVICE_PROP_PAIRED)
    connected = bluetooth_utils.get_device_property(
        path, bluetooth_constants.DEVICE_PROP_CONNECTED)
    service_resolved = bluetooth_utils.get_device_property(
        path, bluetooth_constants.DEVICE_PROP_SERVICES_RESOLVED)

    tv_status[bluetooth_constants.DEVICE_PROP_PAIRED] = paired
    tv_status[bluetooth_constants.DEVICE_PROP_CONNECTED] = connected
    tv_status[bluetooth_constants.DEVICE_PROP_SERVICES_RESOLVED] = service_resolved

    print(
        f"update_state ok, path = {path}, tv_status: \r\nPaired=>{tv_status[bluetooth_constants.DEVICE_PROP_PAIRED]}\r\nConnected=>{tv_status[bluetooth_constants.DEVICE_PROP_CONNECTED]}\r\nServiceResolved=>{tv_status[bluetooth_constants.DEVICE_PROP_SERVICES_RESOLVED]}")

    global g_tivo_rcu_service
    if paired and connected and service_resolved:
        stop_advertising()
        g_tivo_rcu_service.set_connected_device(path)
        print(
            f"{path} connected! TivoRCUService is ready, press any key to send the events.. (press esc to exit")
    else:
        connected_device_path = g_tivo_rcu_service.get_connected_device()
        if connected_device_path == path:
            print(
                f"{path} disconnected, TivoRCUService is not ready, into advertising state")
            start_advertising()
            g_tivo_rcu_service.set_connected_device(None)


"""
When a connection for a device which is already known is established, a PropertiesChanged signal is
instead emitted with the Connected property.
ex:
signal time=1636546346.734315 sender=:1.13 -> destination=(null destination) serial=287
path=/org/bluez/hci0/dev_57_B0_FD_AF_2B_C3; interface=org.freedesktop.DBus.Properties;
member=PropertiesChanged
    string "org.bluez.Device1"
    array [
        dict entry(
            string "ServicesResolved"
            variant boolean false
        )
        dict entry(
            string "Connected"
            variant boolean false
        )
        dict entry(
            string "UUIDs"
            variant array []
        )
    ]
    array [
    ]
"""


def properties_changed(interface, changed, invalidated, path):
    if interface == bluetooth_constants.DEVICE_INTERFACE:
        print(
            f"[[Properties changed, path = {path}")
        if bluetooth_constants.DEVICE_PROP_PAIRED in changed:
            print(
                f"[[Properties changed, Paired:{changed[bluetooth_constants.DEVICE_PROP_PAIRED]}")
        if bluetooth_constants.DEVICE_PROP_CONNECTED in changed:
            print(
                f"[[Properties changed, Connected:{changed[bluetooth_constants.DEVICE_PROP_CONNECTED]}")
        if bluetooth_constants.DEVICE_PROP_SERVICES_RESOLVED in changed:
            print(
                f"[[Properties changed, ServiceResolved:{changed[bluetooth_constants.DEVICE_PROP_SERVICES_RESOLVED]}")

        update_state(path)


"""
When a connection for a previously unknown device is established, an InterfacesAdded signal is
emitted by a device object with properties status.
ex:
signal time=1636540910.588206 sender=:1.13 -> destination=(null destination) serial=53
path=/; interface=org.freedesktop.DBus.ObjectManager; mem
ber=InterfacesAdded
object path "/org/bluez/hci0/dev_7F_3C_14_39_EB_90"
array [
    dict entry(
        string "org.freedesktop.DBus.Introspectable"
        array [
        ]
    )
    dict entry(
        string "org.bluez.Device1"
        array [
            ..
            dict entry(
                string "Connected"
                variant boolean true
            )
            ..
        ]
    )
    ..
]
"""


def interfaces_added(path, interfaces):
    if bluetooth_constants.DEVICE_INTERFACE in interfaces:
        print(
            f"Receive device interfaces added signal, path = {path}")
        properties = interfaces[bluetooth_constants.DEVICE_INTERFACE]
        if (bluetooth_constants.DEVICE_PROP_PAIRED in properties):
            print(
                f"Receive device interfaces added signal, Paired:{properties[bluetooth_constants.DEVICE_PROP_PAIRED]}")
        if (bluetooth_constants.DEVICE_PROP_CONNECTED in properties):
            print(
                f"Receive device interfaces added signal, Connected:{properties[bluetooth_constants.DEVICE_PROP_CONNECTED]}")
        if (bluetooth_constants.DEVICE_PROP_SERVICES_RESOLVED in properties):
            print(
                f"Receive device interfaces added signal, ServiceResolved:{properties[bluetooth_constants.DEVICE_PROP_SERVICES_RESOLVED]}")
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
                            dbus_interface=bluetooth_constants.DBUS_PROPERTIES,
                            signal_name="PropertiesChanged",
                            path_keyword="path")

    bus.add_signal_receiver(interfaces_added,
                            dbus_interface=bluetooth_constants.DBUS_OM_IFACE,
                            signal_name="InterfacesAdded")

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
    global g_gatt_service_manager
    g_gatt_service_manager = dbus.Interface(
        bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_obj),
        bluetooth_constants.GATT_MANAGER_INTERFACE)

    global g_core_application
    g_core_application = QtWidgets.QApplication([])

    global g_tivo_rcu_service
    g_tivo_rcu_service = TivoRCUService(bus)
    g_gatt_service_manager.RegisterApplication(g_tivo_rcu_service.get_path(), {},
                                               reply_handler=register_app_cb,
                                               error_handler=register_app_error_cb)

    g_core_application.exec_()
    if g_gatt_service_manager != None:
        g_gatt_service_manager.UnregisterApplication(
            g_tivo_rcu_service.get_path())
        print('4-1. g_gatt_service_manager.UnregisterApplication(g_tivo_rcu_service.get_path()) ok')
    print('4-2. Apapter power off')
    adapter_props.Set(bluetooth_constants.ADAPTER_INTERFACE,
                      bluetooth_constants.ADAPTER_PROP_POWER, dbus.Boolean(0))
    print('5. Process end')


if __name__ == "__main__":
    main()
