#!/usr/bin/python3
import dbus.service
import bluetooth_constants
from gi.repository import GLib
from ble_base import Descriptor, Characteristic, Service
import tivo_rcu.key_table_constants as ktc


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

    def notify_battery_level(self):
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, {
                               'Value': [dbus.Byte(self.battery_lvl)]}, [])
        self.notifyCnt += 1

    def drain_battery(self):
        if not self.notifying:
            return True
        if (self.notifyCnt > 1):
            return False  # Update battery level 2 times then stop

        if self.battery_lvl > 0:
            self.battery_lvl -= 2
            if self.battery_lvl < 5:
                # self.battery_lvl = 0
                GLib.source_remove(self.timer)

        # print('BatteryLevelCharacteristic, battery Level drained: ' + repr(self.battery_lvl))
        self.notify_battery_level()
        return True

    def ReadValue(self, options):
        print('Battery Level read: ' + repr(self.battery_lvl))
        return [dbus.Byte(self.battery_lvl)]

    def StartNotify(self):
        print('BatteryLevelCharacteristic.StartNotify')

        if self.notifying:
            print('BatteryLevelCharacteristic already notifying, nothing to do')
            return

        self.notifying = True
        self.timer = GLib.timeout_add(1000, self.drain_battery)

    def StopNotify(self):
        print('BatteryLevelCharacteristic StopNotify')

        if not self.notifying:
            print('BatteryLevelCharacteristic not notifying, nothing to do')
            return

        self.notifying = False


class BatteryService(Service):
    """
    Fake Battery service that emulates a draining battery.

    """
    PATH_BASE = bluetooth_constants.BLUEZ_OBJ_ROOT + "batt_service"
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
        self.value = dbus.Array(
            self.MANUFACTURER_NAME.encode(), signature=dbus.Signature('y'))

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
        self.value = dbus.Array(
            self.MODEL_NUMBER.encode(), signature=dbus.Signature('y'))

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

        self.value = dbus.Array(
            self.VERSION_NUMBER.encode(), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read VersionCharacteristic: {self.value}')
        return self.value

class PnpIdCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A50'
    PNP_VAL = [0x02, 0x81, 0x03, 0x04, 0xe0, 0x00,  0x00]

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.CHARACTERISTIC_UUID,
            ["read"],
            service)
        self.value = dbus.Array(
            self.PNP_VAL, signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read Pnp Id: {self.value}')
        return self.value

class DeviceInfoService(Service):

    SERVICE_UUID = '180A'
    PATH_BASE = bluetooth_constants.BLUEZ_OBJ_ROOT + "device_info_service"

    def __init__(self, bus):
        Service.__init__(self, bus, self.PATH_BASE, self.SERVICE_UUID, True)
        self.add_characteristic(ManufacturerNameCharacteristic(bus, 0, self))
        self.add_characteristic(ModelNumberCharacteristic(bus, 1, self))
        self.add_characteristic(VersionCharacteristic(bus, 2, self))
        self.add_characteristic(PnpIdCharacteristic(bus, 3, self))


class ProtocolModeCharacteristic(Characteristic):
    CHARACTERISTIC_UUID = '2A4E'

    def __init__(self, bus, index, service):

        Characteristic.__init__(
            self, bus, index,
            self.CHARACTERISTIC_UUID,
            ["read", "write-without-response"],
            service)

        self.parent = service
        self.value = dbus.Array(bytearray.fromhex(
            '01'), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read ProtocolMode ..')
        return self.value

    def WriteValue(self, value, options):
        print(f'Write ProtocolMode {value}')
        self.value = value


class HIDInfoCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A4A'
    HIDInfo = 'My HID'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.CHARACTERISTIC_UUID,
            ['read'],
            service)
        # self.value = dbus.Array(self.HIDInfo.encode(),
        #                        signature=dbus.Signature('y'))
        self.value = dbus.Array(bytearray.fromhex(
            '01010002'), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read HIDInformation ..')
        return self.value


class ControlPointCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A4C'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.CHARACTERISTIC_UUID,
            ["write-without-response"],
            service)

        self.value = dbus.Array(bytearray.fromhex(
            '00'), signature=dbus.Signature('y'))

    def WriteValue(self, value, options):
        print(f'Write ControlPoint {value}')
        self.value = value


class ReportMapCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A4B'

    def __init__(self, bus, index, service, key_descriptor_obj):
        Characteristic.__init__(
            self, bus, index,
            self.CHARACTERISTIC_UUID,
            ['read'],
            service)

        # USB HID Report Descriptor
        report_map = None
        if key_descriptor_obj is not None and ktc.HID_REPORT_VALUES in key_descriptor_obj:
            report_map = bytes.fromhex(key_descriptor_obj[ktc.HID_REPORT_VALUES])
        self.value = dbus.Array(report_map)

    def ReadValue(self, options):
        print(f'Read ReportMap: {self.value}')
        return self.value


class ReportDescriptor(Descriptor):

    DESCRIPTOR_UUID = '2908'

    def __init__(self, bus, index, characteristic, report_name, report_id):
        Descriptor.__init__(
            self, bus, index,
            self.DESCRIPTOR_UUID,
            ['read'],
            characteristic)
        self.report_name = report_name
        self.report_id = report_id
        '''
        <Field name="Report ID">
            <Requirement>Mandatory</Requirement>
            <Format>uint8</Format>
            <Minimum>0</Minimum>
            <Maximum>255</Maximum>
        </Field>
        
        <Field name="Report Type">
            <Requirement>Mandatory</Requirement>
            <Format>uint8</Format>
            <Minimum>1</Minimum>
            <Maximum>3</Maximum>
            <Enumerations>
                <Enumeration value="Input Report" key="1"/>
                <Enumeration value="Output report" key="2"/>
                <Enumeration value="Feature Report" key="3"/>
                <ReservedForFutureUse start="4" end="255"/>
                <ReservedForFutureUse1 start1="0" end1="0"/>
            </Enumerations>
        </Field>
        '''
        # This uses ReportId (ex:0x0c) in the ReportMap
        input_report_type = '0x01'
        compose_value = bytearray(
            [int(report_id, 16), int(input_report_type, 16)])
        self.value = dbus.Array(compose_value, signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read {self.report_name} Descriptor with value {self.value}')
        return self.value


class ReportCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A4D'

    def __init__(self, bus, index, service, report_name, report_id, report_length):
        Characteristic.__init__(
            self, bus, index,
            self.CHARACTERISTIC_UUID,
            ['secure-read', 'notify'],
            service)
        self.report_name = report_name
        self.report_length = report_length
        '''
        Use standard key codes: https://www.usb.org/sites/default/files/documents/hut1_12v2.pdf
        '''
        self.add_descriptor(ReportDescriptor(
            bus, 1, self, self.report_name, report_id))
        self.value = [dbus.Byte(0) * self.report_length]

    def send(self, key_codes, pressed):
        full_key_code = []
        if pressed:
            key_codes_byte_array = bytearray.fromhex(key_codes)
            full_key_code = [dbus.Byte(key_code_byte)
                             for key_code_byte in key_codes_byte_array]
        else:  # released
            full_key_code = [dbus.Byte(0x00)
                             for _ in range(self.report_length)]

        print(
            f'ReportCharacteristic [{self.report_name}], send full_key_code: {full_key_code}')
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, {
                               'Value': full_key_code}, [])
        print(f'ReportCharacteristic [{self.report_name}], sent')
        return True

    # This is not be read while service registered by central
    def ReadValue(self, options):
        print(f'Read ReportCharacteristic [{self.report_name}] ..')
        return self.value

    # This is supposed not to be workable while central write value directly
    def WriteValue(self, value, options):
        print(f'Write ReportCharacteristic [{self.report_name}] {value}')
        self.value = value

    def StartNotify(self):
        print(
            f'ReportCharacteristic [{self.report_name}] StartNotify() called')

    def StopNotify(self):
        print(f'ReportCharacteristic [{self.report_name}] StopNotify() called')


class HIDService(Service):
    SERVICE_UUID = '1812'
    PATH_BASE = bluetooth_constants.BLUEZ_OBJ_ROOT + "hid_service"

    def __init__(self, bus, key_descriptor_obj):
        Service.__init__(self, bus, self.PATH_BASE, self.SERVICE_UUID, True)
        self.key_descriptor_obj = key_descriptor_obj

        index = 0
        self.protocolMode = ProtocolModeCharacteristic(bus, index, self)
        self.add_characteristic(self.protocolMode)

        index += 1
        self.hidInfo = HIDInfoCharacteristic(bus, index, self)
        self.add_characteristic(self.hidInfo)

        index += 1
        self.controlPoint = ControlPointCharacteristic(bus, index, self)
        self.add_characteristic(self.controlPoint)

        index += 1
        self.reportMap = ReportMapCharacteristic(
            bus, index, self, self.key_descriptor_obj)
        self.add_characteristic(self.reportMap)

        # add report characteristics
        self.report_characteristics = {}
        if self.key_descriptor_obj is not None and ktc.HID_REPORTS in self.key_descriptor_obj:
            hid_reports = self.key_descriptor_obj[ktc.HID_REPORTS]
            for _, (report_key, report_info) in enumerate(hid_reports.items()):
                report_name = report_info[ktc.REPORT_NAME]
                report_id = report_info[ktc.REPORT_ID]
                report_length = report_info[ktc.REPORT_LENGTH]
                index += 1
                report_char = ReportCharacteristic(
                    bus, index, self, report_name, report_id, report_length)
                self.add_characteristic(report_char)
                self.report_characteristics[report_key] = report_char

    def onKeyEvent(self, key_name, pressed):
        key_table = self.key_descriptor_obj[ktc.KEY_TABLE]
        print(
            f'HIDService.onKeyEvent, key_name: {key_name}, pressed: {pressed}')
        if key_name in key_table:
            key_info = key_table[key_name]
            if ktc.REFER_TO_HID_REPORT in key_info and key_info[ktc.REFER_TO_HID_REPORT] in self.report_characteristics:
                dest_rc = self.report_characteristics[key_info[ktc.REFER_TO_HID_REPORT]]
                print(f'HIDService.onKeyEvent, key_name: {key_name} in table')
                dest_rc.send(key_info[ktc.KEY_CODE], pressed)
