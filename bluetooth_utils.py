#!/usr/bin/python3
import bluetooth_constants
import dbus


def get_device_property(path, property_name):
    prop_state = False
    try:
        properties_in_path = dbus.Interface(dbus.SystemBus().get_object(
            bluetooth_constants.BLUEZ_SERVICE_NAME, path), bluetooth_constants.DBUS_PROPERTIES)
        prop_state = properties_in_path.Get(
            bluetooth_constants.DEVICE_INTERFACE, property_name)
    except Exception as e:
        print(f"get_device_property, exception occurs with :{e}")
    return prop_state

def get_object_interface(path, interface_name):
    bus = dbus.SystemBus()
    device_proxy = bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, path)
    device_interface = dbus.Interface(device_proxy, interface_name)
    return device_interface
    
