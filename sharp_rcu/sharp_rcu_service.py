#!/usr/bin/python3
import dbus.service
import bluetooth_constants
import bluetooth_utils
from gi.repository import GLib
from sharp_rcu.ble_hogp import DeviceInfoService, BatteryService, HIDService
from key_event_monitor import KeyEventMonitor
from sharp_rcu.sharp_rcu import SharpRcuDlg
from sharp_rcu.ble_voice_service import VoiceService
import json


class SharpRCUService(dbus.service.Object):
    def __init__(self, bus, exit_listener):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

        # Prepare json object, load configuration from json file.
        key_descriptor_obj = None
        with open('./sharp_rcu/sharp_rcu_descriptor.json', 'r') as f:
            key_descriptor_obj = json.load(f) 

        self.hid_service = HIDService(bus, key_descriptor_obj)
        self.add_service(self.hid_service)

        # Prepare voice service
        self.ruc_dlg = SharpRcuDlg(
            self.onKeyEvent, self.onCaptureKeyboard, key_descriptor_obj, self.onKeyEsc)
        self.voice_service = VoiceService(bus, self.ruc_dlg)
        self.add_service(self.voice_service)
        self.add_service(DeviceInfoService(bus))
        self.add_service(BatteryService(bus))

        self.connected_device_path = None
        self.KeyEventMonitor = KeyEventMonitor(self.onKeyEvent, self.onExit)
        self.KeyEventMonitor.start()

        self.exit_listener = exit_listener

    def get_path(self):
        return dbus.ObjectPath(self.path)
    
    def get_name(self):
        return "SharpRCUService"

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
            self.ruc_dlg.show()
        else:
            self.ruc_dlg.hide()

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
        self.exit_listener()

    def onKeyEsc(self):
        print(f"onKeyEsc begin")
        self.KeyEventMonitor.fireKey('esc')

    def onKeyEvent(self, key_name, pressed):
        if self.connected_device_path:
            self.hid_service.onKeyEvent(key_name, pressed)
            if 'KEY_SHARP_VOICE' == key_name:
                self.voice_service.HTT(pressed)
            elif 'KEY_SHARP_VOICE_SIMULATE' == key_name and pressed == False:
                self.voice_service.simulatingHTT()
        else:
            pass

    def onCaptureKeyboard(self, b_capture):
        self.KeyEventMonitor.setCaptureKeyboard(b_capture)
