#!/usr/bin/python3
import audioop
import bluetooth_constants
from ble_base import Characteristic, Service
import dbus.service
from gi.repository import GLib
import struct
from sharp_rcu.voice_source import DataState, VoiceSource

TV_TX_GET_CAPS = 0x0A
TV_TX_MIC_OPEN = 0x0C
TV_TX_MIC_CLOSE = 0x0D

RCU_CTL_GET_CAP_RESP = 0x0B
RCU_CTL_AUDIO_START = 0x04
RCU_CTL_AUDIO_END = 0x00


class TvTxCharacteristic(Characteristic):
    CHARACTERISTIC_UUID = 'b9524732-bb08-11ec-8422-0242ac120002'

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
        print(f'TvTxCharacteristic.ReadValue')
        return self.value

    def WriteValue(self, value, options):
        print(f'TvTxCharacteristic.WriteValue, value = : {value}')
        self.parent.HandleTvTx(value, options)


class TvRxCharacteristic(Characteristic):
    CHARACTERISTIC_UUID = 'b95249d0-bb08-11ec-8422-0242ac120002'

    def __init__(self, bus, index, service):

        Characteristic.__init__(
            self, bus, index,
            self.CHARACTERISTIC_UUID,
            ['notify'],
            service)

        self.parent = service
        self.value = dbus.Array(bytearray.fromhex(
            '01'), signature=dbus.Signature('y'))

    def StartNotify(self):
        print('TvRxCharacteristic.StartNotify')

    def StopNotify(self):
        print('TvRxCharacteristic.StopNotify')

    def Notify(self, obj):
        # print(f'TvRxCharacteristic.Notify, obj = {obj}')
        self.PropertiesChanged(
            bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, obj, [])


class TvCtlCharacteristic(Characteristic):
    CHARACTERISTIC_UUID = 'b9524b06-bb08-11ec-8422-0242ac120002'

    def __init__(self, bus, index, service):

        Characteristic.__init__(
            self, bus, index,
            self.CHARACTERISTIC_UUID,
            ['notify'],
            service)

        self.parent = service
        self.value = dbus.Array(bytearray.fromhex(
            '01'), signature=dbus.Signature('y'))

    def StartNotify(self):
        print('TvCtlCharacteristic.StartNotify')

    def StopNotify(self):
        print('TvCtlCharacteristic.StopNotify')

    def Notify(self, obj):
        print(f'TvCtlCharacteristic.Notify, obj = {obj}')
        self.PropertiesChanged(
            bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, obj, [])


class VoiceService(Service):
    SERVICE_UUID = 'b9524502-bb08-11ec-8422-0242ac120002'
    PATH_BASE = bluetooth_constants.BLUEZ_OBJ_ROOT + "voice_service"

    def __init__(self, bus, ruc_dlg):
        Service.__init__(self, bus, self.PATH_BASE, self.SERVICE_UUID, True)

        self.voice_source = VoiceSource(ruc_dlg, self.onPCMData)

        self.tv_tx_char = TvTxCharacteristic(bus, 0, self)
        self.add_characteristic(self.tv_tx_char)

        self.tv_rx_char = TvRxCharacteristic(bus, 1, self)
        self.add_characteristic(self.tv_rx_char)

        self.tv_ctl_char = TvCtlCharacteristic(bus, 2, self)
        self.add_characteristic(self.tv_ctl_char)

        # stuff to encode to ADPCM
        self.resetEncodeADPCMState()

    def resetEncodeADPCMState(self):
        self.state = (0, 0x00)
        self.seq = 0

    # split the adpcm data into chunks with each one 20 bytes,
    def NotifyADPCMPktWithHeaderWithChunks(self, adpcm_packet_with_header):
        # separate the adpcm data into chunks with each one 20 bytes,
        # and send it sequentially, each chunk will be notified to the client.
        adpcm_chunk_size = 20
        adpcm_data_len = len(adpcm_packet_with_header)
        chunk_num = adpcm_data_len // adpcm_chunk_size
        idx_chunk = 0
        while idx_chunk < chunk_num:
            chunk = adpcm_packet_with_header[idx_chunk *
                                             adpcm_chunk_size:(idx_chunk+1)*adpcm_chunk_size]
            # self.tv_rx_char.Notify({'Value': chunk})
            self.tv_rx_char.Notify({'Value': chunk})
            idx_chunk += 1

        # send the last chunk
        chunk = adpcm_packet_with_header[idx_chunk *
                                         adpcm_chunk_size:adpcm_data_len]
        self.tv_rx_char.Notify({'Value': chunk})

    def NotifyADPCMPkt(self, adpcm_packet):
        self.tv_rx_char.Notify({'Value': adpcm_packet})

    # receive PCM data from the voice source, encode it to adpcm data and send it to the client.
    # will ended incase receive 0 bytes from the voice source.
    def onPCMData(self, data_state, read_pcm_frames):
        print(
            f'VoiceService.onPCMData called, data_state = {data_state}')
        if data_state == DataState.BEGIN:
            print(
                f'VoiceService.onPCMData begin to send pcmdata, data_state = {data_state}')
            self.resetEncodeADPCMState()

            # HTT Audio transfer is triggered by “Assistant” button press and
            # will stop once the button is released.
            reason = 0x03

            # codec_used = 0x01: ADPCM (8Khz/16bit)
            # codec_used = 0x02: ADPCM (16Khz/16bit)
            codec_used = 1

            # 0x01..0x80:​ an auto-incremented value if the ​ reason ​ field is not 0x00.
            stream_id = 0x80

            audio_start_bytes = struct.pack('>B', RCU_CTL_AUDIO_START) + struct.pack(
                '>B', reason) + struct.pack('>B', codec_used) + struct.pack('>B', stream_id)
            dbus_audio_start_bytes = [dbus.Byte(b) for b in audio_start_bytes]
            self.tv_ctl_char.Notify({'Value': dbus_audio_start_bytes})

        elif data_state == DataState.END:
            print(
                f'VoiceService.onPCMData end, will send end to client')
            # send the audio_end notification
            # triggered by releasing an Assistant button during HTT
            # interaction
            reason = 0x02

            audio_stop_bytes = struct.pack('>B', RCU_CTL_AUDIO_END) + struct.pack(
                '>B', reason)
            dbus_audio_stop_bytes = [dbus.Byte(b) for b in audio_stop_bytes]
            self.tv_ctl_char.Notify({'Value': dbus_audio_stop_bytes})
        elif data_state == DataState.SENDING_DATA:
            if len(read_pcm_frames) > 0:
                dbus_adpcm_data = []
                # encode the pcm data to adpcm data
                adpcm_data, self.state = audioop.lin2adpcm(
                    read_pcm_frames, self.voice_source.getSampleWidth(), self.state)
                print(
                    f'VoiceService.onPCMData, read pcm ok, encoded to ADPCM, len = {len(adpcm_data)}')
                dbus_adpcm_data.extend(
                    [dbus.Byte(b) for b in adpcm_data])
                self.NotifyADPCMPkt(dbus_adpcm_data)
            else:
                print(
                    f'VoiceService.onPCMData receiving data error, len(read_pcm_frames) <= 0!')

    def HandleTvTx(self, value, options):
        print(f'HandleTvTx called, value = {value}')
        command_val = value[0]
        if int(command_val) == TV_TX_GET_CAPS:
            print(f'HandleTvTx, will handle get caps..')
            get_cap_resp_byte = struct.pack('>B', RCU_CTL_GET_CAP_RESP)
            version = 0x0100
            version_bytes = struct.pack('>H', version)
            codec = 1
            codec_byte = struct.pack('>B', codec)
            htt_mode = 3
            htt_mode_byte = struct.pack('>B', htt_mode)
            audio_frame_size = 128
            audio_frame_size_bytes = struct.pack('>H', audio_frame_size)
            dle = 0
            dle_byte = struct.pack('>B', dle)
            reserved = 0
            reserved_byte = struct.pack('>B', reserved)
            get_cap_resp = get_cap_resp_byte + version_bytes + codec_byte + \
                htt_mode_byte + audio_frame_size_bytes + dle_byte + reserved_byte
            dbus_get_cap_resp = [dbus.Byte(b) for b in get_cap_resp]
            self.tv_ctl_char.Notify({'Value': dbus_get_cap_resp})
            print(f'HandleTvTx, handle get caps end')
        print(f'HandleTvTx end')

    def HTT(self, pressed = True):
        if pressed:
            self.voice_source.CaptureVoice(pressed)
        else:
            self.voice_source.CaptureVoice(pressed)

    def simulatingHTT(self):
        self.voice_source.startCaptureThreads()
