#!/usr/bin/python3

from __future__ import absolute_import, print_function, unicode_literals

from gi.repository import GObject

import bluetooth_constants
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
from optparse import OptionParser
from agent import Agent

if __name__ == '__main__':
    capability = "NoInputNoOutput"

    parser = OptionParser()
    parser.add_option("-i", "--adapter", action="store",
                      type="string",
                      dest="adapter_pattern",
                      default=None)
    parser.add_option("-c", "--capability", action="store",
                      type="string", dest="capability")
    parser.add_option("-t", "--timeout", action="store",
                      type="int", dest="timeout",
                      default=60000)
    (options, args) = parser.parse_args()
    if options.capability:
        capability = options.capability
    
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    
    AGENT_PATH = bluetooth_constants.BLUEZ_OBJ_ROOT + "agent"
    agent = Agent(bus, AGENT_PATH)

    agent_manager = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, '/org/bluez'),
                                   bluetooth_constants.AGENT_MANAGER_INTERFACE)
    agent_manager.RegisterAgent(AGENT_PATH, capability)

    print("Agent registered")

    g_mainloop = GLib.MainLoop()
    g_mainloop.run()

    # adapter.UnregisterAgent(path)
    # print("Agent unregistered")
