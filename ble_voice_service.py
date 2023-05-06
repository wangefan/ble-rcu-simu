#!/usr/bin/python3
import audioop
import bluetooth_constants
from ble_base import Characteristic, Service
import dbus.service
from gi.repository import GLib
import struct
from voice_source import DataState, VoiceSource

TV_TX_GET_CAPS = 0x0A
TV_TX_MIC_OPEN = 0x0C
TV_TX_MIC_CLOSE = 0x0D

RCU_CTL_GET_CAP_RESP = 0x0B
RCU_CTL_START_SEARCH = 0x08
RCU_CTL_AUDIO_START = 0x04
RCU_CTL_AUDIO_END = 0x00


class TivoTvTxCharacteristic(Characteristic):
    CHARACTERISTIC_UUID = 'ab5e0002-5a21-4f05-bc7d-af01f617b664'

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
        print(f'TivoTvTxCharacteristic.ReadValue')
        return self.value

    def WriteValue(self, value, options):
        print(f'TivoTvTxCharacteristic.WriteValue, value = : {value}')
        self.parent.HandleTvTx(value, options)


class TivoTvRxCharacteristic(Characteristic):
    CHARACTERISTIC_UUID = 'ab5e0003-5a21-4f05-bc7d-af01f617b664'

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
        print('TivoTvRxCharacteristic.StartNotify')

    def StopNotify(self):
        print('TivoTvRxCharacteristic.StopNotify')

    def Notify(self, obj):
        # print(f'TivoTvRxCharacteristic.Notify, obj = {obj}')
        self.PropertiesChanged(
            bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, obj, [])


class TivoTvCtlCharacteristic(Characteristic):
    CHARACTERISTIC_UUID = 'ab5e0004-5a21-4f05-bc7d-af01f617b664'

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
        print('TivoTvCtlCharacteristic.StartNotify')

    def StopNotify(self):
        print('TivoTvCtlCharacteristic.StopNotify')

    def Notify(self, obj):
        print(f'TivoTvCtlCharacteristic.Notify, obj = {obj}')
        self.PropertiesChanged(
            bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, obj, [])


class VoiceService(Service):
    SERVICE_UUID = 'ab5e0001-5a21-4f05-bc7d-af01f617b664'
    PATH_BASE = bluetooth_constants.BLUEZ_OBJ_ROOT + "tivo_voice_service"

    def __init__(self, bus, tivo_ruc_dlg):
        Service.__init__(self, bus, self.PATH_BASE, self.SERVICE_UUID, True)

        self.voice_source = VoiceSource(tivo_ruc_dlg, self.onPCMData)

        self.tivo_tv_tx_char = TivoTvTxCharacteristic(bus, 0, self)
        self.add_characteristic(self.tivo_tv_tx_char)

        self.tivo_tv_rx_char = TivoTvRxCharacteristic(bus, 1, self)
        self.add_characteristic(self.tivo_tv_rx_char)

        self.tivo_tv_ctl_char = TivoTvCtlCharacteristic(bus, 2, self)
        self.add_characteristic(self.tivo_tv_ctl_char)

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
            # self.tivo_tv_rx_char.Notify({'Value': chunk})
            self.tivo_tv_rx_char.Notify({'Value': chunk})
            idx_chunk += 1

        # send the last chunk
        chunk = adpcm_packet_with_header[idx_chunk *
                                         adpcm_chunk_size:adpcm_data_len]
        self.tivo_tv_rx_char.Notify({'Value': chunk})

    def NotifyADPCMPktWithHeader(self, adpcm_packet_with_header):
        self.tivo_tv_rx_char.Notify({'Value': adpcm_packet_with_header})

    # receive PCM data from the voice source, encode it to adpcm data and send it to the client.
    # will ended incase receive 0 bytes from the voice source.
    def onPCMData(self, data_state, read_pcm_frames):
        print(
            f'VoiceService.onPCMData called, data_state = {data_state}')
        if data_state == DataState.BEGIN:
            # todo: send begin notification
            print(
                f'VoiceService.onPCMData begin to send pcmdata, data_state = {data_state}')
            self.resetEncodeADPCMState()
        elif data_state == DataState.END:
            print(
                f'VoiceService.onPCMData end, will send end to client')
            # send the end notification
            audio_end_byte = struct.pack('>B', RCU_CTL_AUDIO_END)
            dbus_audio_end_byte = [dbus.Byte(audio_end_byte)]
            self.tivo_tv_ctl_char.Notify({'Value': dbus_audio_end_byte})
        elif data_state == DataState.SENDING_DATA:
            if len(read_pcm_frames) > 0:
                # adpcm_data_with_header will append 6 bytes header and 128 bytes adpcm data.
                # header structure: [seq hi, seq lo, rcuid, pre predict hi, pre predict lo, pre index]
                adpcm_header_bytes = struct.pack(
                    '>H', self.seq) + struct.pack('B', 0x00) + struct.pack('>h', self.state[0]) + struct.pack('B', self.state[1])
                adpcm_data_with_header = [
                    dbus.Byte(b) for b in adpcm_header_bytes]
                self.seq += 1

                # encode the pcm data to adpcm data
                adpcm_data, self.state = audioop.lin2adpcm(
                    read_pcm_frames, self.voice_source.getSampleWidth(), self.state)
                print(
                    f'VoiceService.onPCMData, read pcm ok, encoded to ADPCM, len = {len(adpcm_data)}')
                adpcm_data_with_header.extend(
                    [dbus.Byte(b) for b in adpcm_data])
                self.NotifyADPCMPktWithHeader(adpcm_data_with_header)
            else:
                print(
                    f'VoiceService.onPCMData receiving data error, len(read_pcm_frames) <= 0!')

    def HandleTvTx(self, value, options):
        print(f'HandleTvTx called, value = {value}')
        command_val = value[0]
        if int(command_val) == TV_TX_GET_CAPS:
            print(f'HandleTvTx, will handle get caps..')
            get_cap_resp_byte = struct.pack('>B', RCU_CTL_GET_CAP_RESP)
            version = 4
            version_bytes = struct.pack('>H', version)
            codec = 3
            codec_bytes = struct.pack('>H', codec)
            bytes_per_frame = 134
            bytes_per_frame_bytes = struct.pack('>H', bytes_per_frame)
            bytes_per_char = 20
            bytes_per_char_bytes = struct.pack('>H', bytes_per_char)

            get_cap_resp = get_cap_resp_byte + version_bytes + codec_bytes + \
                bytes_per_frame_bytes + bytes_per_char_bytes
            dbus_get_cap_resp = [dbus.Byte(b) for b in get_cap_resp]
            self.tivo_tv_ctl_char.Notify({'Value': dbus_get_cap_resp})
            print(f'HandleTvTx, handle get caps end')
        elif int(command_val) == TV_TX_MIC_OPEN:
            print(f'HandleTvTx, will handle mic open..')
            # There are 2 cases here, one is the mic open successful with intended parameters,
            # would response with audio start, the other is the mic open failed and response
            # with error code. Both are notified by self.tivo_tv_ctl_char.

            # mic_open_params = 1: ADPCM (8Khz/16bit)
            # mic_open_params = 2: ADPCM (16Khz/16bit)
            mic_open_params = (int)(value[2])
            if mic_open_params == 1:
                print(f'HandleTvTx, mic_open_params:ADPCM (8Khz/16bit)')
            elif mic_open_params == 2:
                print(f'HandleTvTx, mic_open_params:ADPCM (16Khz/16bit)')

            # Todo:error case is not implemented yet
            mic_open_resp = struct.pack('>B', RCU_CTL_AUDIO_START)
            dbus_mic_open_resp = [dbus.Byte(mic_open_resp)]
            self.tivo_tv_ctl_char.Notify({'Value': dbus_mic_open_resp})

            # start to capture voice with worker thread, will receive pcm data from
            # the callback onPCMData
            self.voice_source.startCaptureVoice(mic_open_params)
            print(f'HandleTvTx, handle mic open end')

        elif int(command_val) == TV_TX_MIC_CLOSE:
            print(f'HandleTvTx, handle mic close end')

        print(f'HandleTvTx end')

    def VoiceSearch(self):
        start_search_byte = struct.pack('>B', RCU_CTL_START_SEARCH)
        dbus_start_search_byte = [dbus.Byte(start_search_byte)]
        self.tivo_tv_ctl_char.Notify({'Value': dbus_start_search_byte})
