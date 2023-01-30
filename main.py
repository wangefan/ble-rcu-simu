#!/usr/bin/python3
import dbus
import dbus.exceptions
import dbus.service
from gi.repository import GLib
try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject

import dbus.mainloop.glib
import bluetooth_constants
import bluetooth_exceptions

g_mainloop = None


def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, '/'),
                               bluetooth_constants.DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if bluetooth_constants.GATT_MANAGER_INTERFACE in props.keys():
            return o

    return None


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    adapter = find_adapter(bus)
    if not adapter:
        print('GattManager1 interface not found')
        return
    service_manager = dbus.Interface(
        bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, adapter),
        bluetooth_constants.GATT_MANAGER_INTERFACE)

    global g_mainloop
    g_mainloop = GObject.MainLoop()

    g_mainloop.run()


if __name__ == "__main__":
    main()
