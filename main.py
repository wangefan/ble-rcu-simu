#!/usr/bin/python3
import bluetooth_constants
import dbus.mainloop.glib
from gi.repository import GLib
import dbus
import dbus.exceptions
import dbus.service
from sharp_rcu.advertise import SharpRCUAdvertisement
from sharp_rcu.sharp_rcu_service import SharpRCUService
from tivo_rcu.advertise import TiVoS4KRCUAdvertisement
from tivo_rcu.tivo_rcu_service import TivoRCUService
from agent import Agent
import argparse
import bluetooth_utils
from PyQt5 import QtCore, QtWidgets

g_core_application = None
g_ad_manager = None
g_gatt_service_manager = None
g_rcu_advertisement = None
g_rcu_service = None
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

    global g_rcu_service
    if paired and connected and service_resolved:
        stop_advertising()
        g_rcu_service.set_connected_device(path)
        print(
            f"{path} connected! {g_rcu_service.get_name()} is ready, press any key to send the events.. (press esc to exit")
    else:
        connected_device_path = g_rcu_service.get_connected_device()
        if connected_device_path == path:
            print(
                f"{path} disconnected, {g_rcu_service.get_name()} is not ready, into advertising state")
            start_advertising()
            g_rcu_service.set_connected_device(None)


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
    parser.add_argument('-io', dest='io_capability_type', nargs='?', type=int, default=0,
                        help='Specify the IO capability of the device, 0: NoInputNoOutput, 1: DisplayYesNo, 2: KeyboardDisplay, 3: DisplayOnly, 4:  KeyboardOnly')
    parser.add_argument('-rc', dest='rc_type', nargs='?', type=int, default=0,
                        help='Specify RCU type, 0: Sharp, 1: TiVo Remote')
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

    rc_type = args.rc_type

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

    global g_core_application
    g_core_application = QtWidgets.QApplication([])

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
    
    global g_rcu_advertisement
    global g_rcu_service
    
    
    if rc_type == 1:
        g_rcu_advertisement = TiVoS4KRCUAdvertisement(bus, mac_address, 0)
        g_rcu_service = TivoRCUService(bus, closeAll) # Fix me, factory to get TivoRCUService
        adapter_props.Set(bluetooth_constants.ADAPTER_INTERFACE,
                      bluetooth_constants.ADAPTER_PROP_ALIAS, dbus.String(
                          TiVoS4KRCUAdvertisement.DISCOVERABLE_NAME))
    elif rc_type == 0:
        g_rcu_advertisement = SharpRCUAdvertisement(bus, mac_address, 0)
        g_rcu_service = SharpRCUService(bus, closeAll) # Fix me, factory to get SharpRCUService
        adapter_props.Set(bluetooth_constants.ADAPTER_INTERFACE,
                      bluetooth_constants.ADAPTER_PROP_ALIAS, dbus.String(
                          SharpRCUAdvertisement.DISCOVERABLE_NAME))

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
    start_advertising()

    print('4. Registering GATT procedure')
    global g_gatt_service_manager
    g_gatt_service_manager = dbus.Interface(
        bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_obj),
        bluetooth_constants.GATT_MANAGER_INTERFACE)

    g_gatt_service_manager.RegisterApplication(g_rcu_service.get_path(), {},
                                               reply_handler=register_app_cb,
                                               error_handler=register_app_error_cb)

    g_core_application.exec_()
    if g_gatt_service_manager != None:
        g_gatt_service_manager.UnregisterApplication(
            g_rcu_service.get_path())
        print('4-1. g_gatt_service_manager.UnregisterApplication(g_rcu_service.get_path()) ok')
    print('4-2. Apapter power off')
    adapter_props.Set(bluetooth_constants.ADAPTER_INTERFACE,
                      bluetooth_constants.ADAPTER_PROP_POWER, dbus.Boolean(0))
    print('5. Process end')


if __name__ == "__main__":
    main()
