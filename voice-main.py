import argparse

import dbus
import wave
import audioop
import threading, queue

bleQ = queue.Queue() #receiver queue to save adpcm packet to file
decoderQ = queue.Queue() #decoder queue to decode adpcm file into wav file

ble_packets_array = bytearray()
ble_packets_array_to_write = bytearray()

RCU_VERSION_0_4 = 0
RCU_VERSION_1_0 = 1
rcu_version = RCU_VERSION_0_4

try:
  from gi.repository import GObject
  from gi.repository import GLib
except ImportError:
  import gobject as GObject
import sys

from dbus.mainloop.glib import DBusGMainLoop

bus = None
mainloop = None

BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_OM_IFACE =      'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE =    'org.freedesktop.DBus.Properties'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE =    'org.bluez.GattCharacteristic1'

VOICE_SERVICE_INFO = {
    'ab5e0001-5a21-4f05-bc7d-af01f617b664': {
        'CHAR_TX_UUID': 'ab5e0002-5a21-4f05-bc7d-af01f617b664',
        'CHAR_RX_UUID': 'ab5e0003-5a21-4f05-bc7d-af01f617b664',
        'CHAR_CTL_UUID': 'ab5e0004-5a21-4f05-bc7d-af01f617b664',
    },
    'b9524502-bb08-11ec-8422-0242ac120002': {
        'CHAR_TX_UUID': 'b9524732-bb08-11ec-8422-0242ac120002',
        'CHAR_RX_UUID': 'b95249d0-bb08-11ec-8422-0242ac120002',
        'CHAR_CTL_UUID': 'b9524b06-bb08-11ec-8422-0242ac120002',
    }
}

ATV_CTL_AUDIO_END = 0x00
ATV_CTL_AUDIO_START = 0x04
ATV_CTL_SEARCH = 0x08
ATV_CTL_AUDIO_SYNC = 0x0A
ATV_CTL_GET_CAPS_RESP = 0x0B
ATV_CTL_MIC_OPEN_RESP = 0x0C

ATV_TX_GET_CAPS = 0x0A
ATV_TX_MIC_OPEN = 0x0C  #follow by codec used
ATV_TX_MIC_CLOSE = 0x0D

AUDIO_FRAME_LENGTH=134 #6bytes header + 128 bytes adpcm data

# The objects that we interact with.
atv_service = None
atv_ctl_chrc = None
atv_rx_chrc = None
atv_tx_chrc = None

adpcm_filename = 'adpcmRecorded.ima'
wav_filename = 'decoded_out.wav'
sampleRate = 8000

def generic_error_cb(error):
    print('D-Bus call failed: ' + str(error))
    mainloop.quit()

def send_get_caps_cmd_0_4():
    #Get cap (0x0A), 0x00,0x04 (v0.4), 0x00,0x01 (8Khz 16bits)
    cmd_get_caps = bytearray([ATV_TX_GET_CAPS, 0x00, 0x04, 0x00, 0x01])
    atv_tx_chrc[0].WriteValue(cmd_get_caps, {}, dbus_interface=GATT_CHRC_IFACE)
    print('CTL Get CAPS send:')
    print(''.join('{:02x}'.format(x) for x in cmd_get_caps))

def send_get_caps_cmd_1_0():
    #Get cap (0x0A), 0x01, 0x00 (v1.0), 0x00, 0x03 (constant value that is used for compatibility with the previous spec.))
    cmd_get_caps = bytearray([ATV_TX_GET_CAPS, 0x01, 0x00, 0x00, 0x03, 0x03])
    atv_tx_chrc[0].WriteValue(cmd_get_caps, {}, dbus_interface=GATT_CHRC_IFACE)
    print('CTL Get CAPS send:')
    print(''.join('{:02x}'.format(x) for x in cmd_get_caps))

def atv_ctl_notify_cb():
    print('ATV CTL Notifications enabled')
    global rcu_version
    if rcu_version == RCU_VERSION_0_4:
        send_get_caps_cmd_0_4()
    elif rcu_version == RCU_VERSION_1_0:
        send_get_caps_cmd_1_0()


def atv_rx_notify_cb():
    print('ATV RX Notifications enabled')

def atv_tx_resp_cb(value):
    if len(value) == 0:
        print('Invalid value:')
        return

    print('TX Resp value: ' + value[0])
#This callback comes with control command sequence, such as "search", "audio start", "audio end", etc.
#After receiving the "search" command, we need to respond using mic_open with codec_used in TX char
def atv_ctl_changed_cb(iface, changed_props, invalidated_props):
    if iface != GATT_CHRC_IFACE:
        return

    if not len(changed_props):
        return

    value = changed_props.get('Value', None)
    if not value:
        return

    print('New CTL event')

    flags = value[0]

    #cmd_mic_open = bytearray([ATV_TX_MIC_OPEN, 0x00, 0x01])  #0C0001 open mic with 8k 16bit config
    paramValue = 0x01
    if sampleRate == 16000:
        paramValue = 0x02

    cmd_mic_open = bytearray([ATV_TX_MIC_OPEN, 0x00, paramValue])  # 0C0001 open mic with 16k 16bit config

    if int(flags) == ATV_CTL_SEARCH:
        print('CTL Search command received')
        atv_tx_chrc[0].WriteValue(cmd_mic_open,{}, dbus_interface=GATT_CHRC_IFACE)

    if int(flags) == ATV_CTL_AUDIO_START:
        print('CTL Audio Start command received')

    if int(flags) == ATV_CTL_AUDIO_SYNC:
        print('####### CTL Audio Sync received')

    if int(flags) == ATV_CTL_AUDIO_END:
        print('CTL Audio End command received')
        #To trigger decoder worker to decode
        decoderQ.put(flags)

    if int(flags) == ATV_CTL_GET_CAPS_RESP:
        major_ver = int(value[1])
        minor_ver = int(value[2])
        codec_cap = int()
        print('CTL Get CAPS RESP received:')
        print(''.join('{:02x}'.format(x) for x in value[:9]))
        global rcu_version
        global AUDIO_FRAME_LENGTH
        if major_ver == 0 and minor_ver == 0x04:
            print('CTL Get CAPS RESP v0.4 received')
            rcu_version = RCU_VERSION_0_4
            AUDIO_FRAME_LENGTH = 134 # 6bytes header + 128 bytes adpcm data
        elif major_ver == 0 and minor_ver == 0x10:
            print('CTL Get CAPS RESP v1.0 received')
            rcu_version = RCU_VERSION_1_0
            AUDIO_FRAME_LENGTH = 128 #128 bytes adpcm data without header
        elif major_ver == 0x01 and minor_ver == 0x01:
            print('CTL Get CAPS RESP v1.1 received')
            rcu_version = RCU_VERSION_1_0
            AUDIO_FRAME_LENGTH = 128 #128 bytes adpcm data without header
        else:
            print('CTL Get CAPS RESP unknown version received')

    if int(flags) == ATV_CTL_MIC_OPEN_RESP:
        print('CTL MIC Open RESP received')

def decoder_worker():
    while True:
        item = decoderQ.get()
        _adpcmstate = None
        with open(adpcm_filename, "rb") as f:
            with wave.open(wav_filename, "wb") as wav:
                wav.setnchannels(1)  # mono
                wav.setsampwidth(2)  # 16 bits
                wav.setframerate(sampleRate)  # SampleRate
            while True:
                chunk = f.read(128)
                if chunk:
                    pcmData, _adpcmstate = audioop.adpcm2lin(chunk, 2, _adpcmstate)
                    with open(wav_filename, "ab") as w:
                        w.write(pcmData)
                else:
                    break
        decoderQ.task_done()



def ble_worker():
    global ble_packets_array
    global ble_packets_array_to_write
    while True:
        item = bleQ.get()
        print(f'Working on item')
        print(''.join('{:02x}'.format(x) for x in item))
        print(f'Finished item')
        ble_packets_array.extend(bytes(item))
        l = len(ble_packets_array)
        if l >= AUDIO_FRAME_LENGTH:
            ble_packets_array_to_write.extend(ble_packets_array[0:AUDIO_FRAME_LENGTH])
            ble_packets_array = ble_packets_array[AUDIO_FRAME_LENGTH:]
            print(f'write to file: {adpcm_filename} with{AUDIO_FRAME_LENGTH} bytes')
            with open(adpcm_filename, 'ab') as w:
                if rcu_version == RCU_VERSION_0_4:
                    w.write(ble_packets_array_to_write[6:]) # exclude the 6 bytes header while writing
                else:
                    w.write(ble_packets_array_to_write)
            ble_packets_array_to_write.clear() #clear itself after one complete frame

        bleQ.task_done()


def process_ble_packets(blePackets):
    dataLen = len(blePackets)
    print('audio data length: ' + str(dataLen))
    #To trigger ble Queue
    bleQ.put(blePackets)

#This callback comes with compressed audio data with headers
def atv_rx_changed_cb(iface, changed_props, invalidated_props):
    if iface != GATT_CHRC_IFACE:
        return

    if not len(changed_props):
        return

    value = changed_props.get('Value', None)
    if not value:
        return

    print('New RX edata')
    process_ble_packets(value)

    return

def start_atv_client():
    # Listen to PropertiesChanged signals from the ATV CTL Characteristic.
    atv_ctl_prop_iface = dbus.Interface(atv_ctl_chrc[0], DBUS_PROP_IFACE)
    atv_ctl_prop_iface.connect_to_signal("PropertiesChanged",
                                          atv_ctl_changed_cb)
    # Subscribe to ATV CTL notifications.
    atv_ctl_chrc[0].StartNotify(reply_handler=atv_ctl_notify_cb,
                                 error_handler=generic_error_cb,
                                 dbus_interface=GATT_CHRC_IFACE)

    # Listen to PropertiesChanged signals from the ATV RX Characteristic.
    atv_rx_prop_iface = dbus.Interface(atv_rx_chrc[0], DBUS_PROP_IFACE)
    atv_rx_prop_iface.connect_to_signal("PropertiesChanged",
                                          atv_rx_changed_cb)
    # Subscribe to ATV CTL notifications.
    atv_rx_chrc[0].StartNotify(reply_handler=atv_rx_notify_cb,
                                 error_handler=generic_error_cb,
                                 dbus_interface=GATT_CHRC_IFACE)

def process_atv_chrc(chrc_path, service_uuids_info):
    chrc = bus.get_object(BLUEZ_SERVICE_NAME, chrc_path)
    chrc_props = chrc.GetAll(GATT_CHRC_IFACE,
                             dbus_interface=DBUS_PROP_IFACE)

    uuid = chrc_props['UUID']

    if uuid == service_uuids_info['CHAR_CTL_UUID']:
        global atv_ctl_chrc
        atv_ctl_chrc = (chrc, chrc_props)
        print('found ATV CTL characteristic: ' + uuid)
    elif uuid == service_uuids_info['CHAR_TX_UUID']:
        global atv_tx_chrc
        atv_tx_chrc = (chrc, chrc_props)
        print('found ATV TX characteristic: ' + uuid)
    elif uuid == service_uuids_info['CHAR_RX_UUID']:
        global atv_rx_chrc
        atv_rx_chrc = (chrc, chrc_props)
        print('found ATV RX characteristic: ' + uuid)
    else:
        print('Unrecognized characteristic: ' + uuid)

    return True

def process_atv_service(service_path, chrc_paths):
    service = bus.get_object(BLUEZ_SERVICE_NAME, service_path)
    service_props = service.GetAll(GATT_SERVICE_IFACE,
                                   dbus_interface=DBUS_PROP_IFACE)

    uuid = service_props['UUID']

    if uuid not in VOICE_SERVICE_INFO.keys():
        return False

    print('ATV Service found: ' + service_path)
    service_uuids_info = VOICE_SERVICE_INFO[uuid]

    # Process the characteristics.
    for chrc_path in chrc_paths:
        process_atv_chrc(chrc_path, service_uuids_info)

    global atv_service
    atv_service = (service, service_props, service_path)

    return True

def interfaces_removed_cb(object_path, interfaces):
    if not atv_service:
        return

    if object_path == atv_service[2]:
        print('ATV Service was removed')
        mainloop.quit()


def main():
    # Set up the main loop.
    DBusGMainLoop(set_as_default=True)
    global bus
    bus = dbus.SystemBus()
    global mainloop
    mainloop = GLib.MainLoop()

    om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'), DBUS_OM_IFACE)
    om.connect_to_signal('InterfacesRemoved', interfaces_removed_cb)

    print('Getting objects...')
    objects = om.GetManagedObjects()
    chrcs = []

    # List characteristics found
    for path, interfaces in objects.items():
        if GATT_CHRC_IFACE not in interfaces.keys():
            continue
        chrcs.append(path)

    # List sevices found
    for path, interfaces in objects.items():
        if GATT_SERVICE_IFACE not in interfaces.keys():
            continue

        chrc_paths = [d for d in chrcs if d.startswith(path + "/")]

        if process_atv_service(path, chrc_paths):
            break

    if not atv_service:
        print('No ATV Service found')
        sys.exit(1)

    # turn-on the receiver worker thread
    threading.Thread(target=ble_worker, daemon=True).start()

    threading.Thread(target=decoder_worker, daemon=True).start()

    start_atv_client()

    mainloop.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test Voice from S4K RCU')
    parser.add_argument('-s', dest='SampleRate', nargs='?', type=int,help='Specify the intended sampling rate, 0:8Khz (default), 1:16Khz')
    args = parser.parse_args()

    srChoice = args.SampleRate

    if srChoice == 1:
        sampleRate = 16000
    else:
        sampleRate = 8000

    main()

