#!/usr/bin/python3
from tivo_rcu import TivoRcuDlg
import wave
import os
from enum import Enum
import threading
import time
import alsaaudio

ENCODE_ADPCM_CHUNK_SIZE = 128
ENCODE_PCM_TO_ADPCM_FAC = 4
ENCODE_ADPCM_SAMPLE_RATE_8k = 8000
ENCODE_ADPCM_SAMPLE_RATE_16k = 16000
ENCODE_ADPCM_CHANNELS = 1
ENCODE_ADPCM_SAMPLE_WIDTH = 2
RECORD_SECONDS = 6


class DataState(Enum):
    BEGIN = 0
    SENDING_DATA = 1
    END = 2


class VoiceSource:

    def __init__(self, tivo_ruc_dlg, onPCMDataCb):
        self.tivo_ruc_dlg = tivo_ruc_dlg
        self.mic_open_params = 1
        self.condition = None
        self.read_frames_list = []
        self.capture_end = True
        self.onPCMDataCb = onPCMDataCb

    def getSampleWidth(self):
        return ENCODE_ADPCM_SAMPLE_WIDTH

    def consumePCM(self):
        print(f"VoiceSource.consumePCM begin")
        if self.onPCMDataCb != None:
            self.onPCMDataCb(DataState.BEGIN, None)
        while True:
            temp_read_frames_list = None
            temp_capture_end = False
            with self.condition:
                while self.capture_end == False and len(self.read_frames_list) == 0:
                    print(f"VoiceSource.consumePCM wait")
                    self.condition.wait()
                    print(
                        f"VoiceSource.consumePCM wake in loop, self.capture_end = {self.capture_end}, len(self.read_frames_list) = {len(self.read_frames_list)}")

                len_read_frames_list = len(self.read_frames_list)
                temp_read_frames_list = [self.read_frames_list.pop(
                    0) for i in range(len_read_frames_list)]
                temp_capture_end = self.capture_end

            if temp_read_frames_list != None and self.onPCMDataCb != None:
                for frames in temp_read_frames_list:
                    self.onPCMDataCb(DataState.SENDING_DATA, frames)

            if temp_capture_end == True:
                break

        if self.onPCMDataCb != None:
            self.onPCMDataCb(DataState.END, None)

    def producePCMByCapture(self):
        sample_rate = ENCODE_ADPCM_SAMPLE_RATE_8k
        if self.mic_open_params == 1:
            sample_rate = ENCODE_ADPCM_SAMPLE_RATE_8k
        elif self.mic_open_params == 2:
            sample_rate = ENCODE_ADPCM_SAMPLE_RATE_16k

        pcm_frame_size = ENCODE_ADPCM_SAMPLE_WIDTH * ENCODE_ADPCM_CHANNELS
        expected_pcm_frames_num = ENCODE_ADPCM_CHUNK_SIZE * \
            ENCODE_PCM_TO_ADPCM_FAC // pcm_frame_size

        # 初始化錄音
        audio = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK,
                              channels=ENCODE_ADPCM_CHANNELS, rate=sample_rate, format=alsaaudio.PCM_FORMAT_S16_LE,
                              periodsize=expected_pcm_frames_num, device='plughw:CARD=PCH,DEV=0')

        capture_begin_time = time.time()
        while True:
            with self.condition:
                read_pcm_frames_num, read_frames = audio.read() # read_frames_size =256, len(read_frames) = 512
                if read_pcm_frames_num <= 0:
                    continue
                # if read_pcm_frames_num == 0 or read_pcm_frames_num < expected_pcm_frames_num:
                #    print(f'producePCMByCapture error, read_pcm_frames_num:{read_pcm_frames_num}, will break')
                #    self.capture_end = True
                #    self.condition.notify()
                #    break
                capture_elapse_time = time.time() - capture_begin_time
                print(
                    f"producePCMByCapture, read_pcm_frames_num:{read_pcm_frames_num}, capture_elapse_time:{capture_elapse_time}")
                if capture_elapse_time > RECORD_SECONDS:
                    print(
                        f'producePCMByCapture, capture_elapse_time:{capture_elapse_time}, will break')
                    self.capture_end = True
                    self.condition.notify()
                    break
                self.read_frames_list.append(read_frames)
                print(
                    f'producePCMByCapture, len(self.read_frames_list):{len(self.read_frames_list)}')
                self.condition.notify()

    def producePCMByCapture_bk(self):
        sample_rate = ENCODE_ADPCM_SAMPLE_RATE_8k
        if self.mic_open_params == 1:
            sample_rate = ENCODE_ADPCM_SAMPLE_RATE_8k
        elif self.mic_open_params == 2:
            sample_rate = ENCODE_ADPCM_SAMPLE_RATE_16k

        pcm_frame_size = ENCODE_ADPCM_SAMPLE_WIDTH * ENCODE_ADPCM_CHANNELS
        expected_pcm_frames_num = ENCODE_ADPCM_CHUNK_SIZE * \
            ENCODE_PCM_TO_ADPCM_FAC // pcm_frame_size

        # 初始化錄音
        audio = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK,
                              channels=ENCODE_ADPCM_CHANNELS, rate=sample_rate, format=alsaaudio.PCM_FORMAT_S16_LE,
                              periodsize=expected_pcm_frames_num, device='plughw:CARD=PCH,DEV=0')

        capture_begin_time = time.time()
        with self.condition:
            while True:
                read_pcm_frames_num, read_frames = audio.read() # read_frames_size =256, len(read_frames) = 512
                if read_pcm_frames_num <= 0:
                    continue
                capture_elapse_time = time.time() - capture_begin_time
                print(
                    f"producePCMByCapture, read_pcm_frames_num:{read_pcm_frames_num}, capture_elapse_time:{capture_elapse_time}")
                if capture_elapse_time > RECORD_SECONDS:
                    print(
                        f'producePCMByCapture, capture_elapse_time:{capture_elapse_time}, will break')
                    self.capture_end = True
                    self.condition.notify()
                    break
                self.read_frames_list.append(read_frames)
                print(
                    f'producePCMByCapture, len(self.read_frames_list):{len(self.read_frames_list)}')
                

    def producePCMByFile(self):
        wave_file = None

        if self.mic_open_params == 1:
            wave_file = self.tivo_ruc_dlg.get_8k_file_path()
        elif self.mic_open_params == 2:
            wave_file = self.tivo_ruc_dlg.get_16k_file_path()
        else:
            with self.condition:
                self.capture_end = True
                self.read_frames_list = []
                self.condition.notify()
            return

        if os.path.exists(wave_file) == False:
            with self.condition:
                self.capture_end = True
                self.read_frames_list = []
                self.condition.notify()
            return

        with wave.open(wave_file, 'rb') as f:
            print(
                f'producePCMByFile, open file = {wave_file}, channels = {f.getnchannels()}, sample_width = {f.getsampwidth()}, sample_rate = {f.getframerate()}')

            pcm_frame_size = f.getsampwidth() * f.getnchannels()
            expected_pcm_frames_num = ENCODE_ADPCM_CHUNK_SIZE * \
                ENCODE_PCM_TO_ADPCM_FAC // pcm_frame_size
            print(
                f'producePCMByFile, expected_pcm_frames_num:{expected_pcm_frames_num}')

            while True:
                # if len(self.read_frames_list) > 200:
                #    print(f'producePCMByFile, len(self.read_frames_list) > 200!')
                #    time.sleep(0.01)
                with self.condition:
                    read_frames = f.readframes(expected_pcm_frames_num)
                    read_pcm_frames_num = len(read_frames) // pcm_frame_size
                    if read_pcm_frames_num == 0 or read_pcm_frames_num < expected_pcm_frames_num:
                        print(
                            f'producePCMByFile read_pcm_frames_num:{read_pcm_frames_num}, will break')
                        self.capture_end = True
                        self.condition.notify()
                        break
                    self.read_frames_list.append(read_frames)
                    print(
                        f'producePCMByFile, len(self.read_frames_list):{len(self.read_frames_list)}')
                    self.condition.notify()

    # mic_open_params = 1: ADPCM (8Khz/16bit)
    # mic_open_params = 2: ADPCM (16Khz/16bit)
    def startCaptureVoice(self, mic_open_params):
        self.mic_open_params = mic_open_params
        print(
            f"VoiceSource.startCaptureVoice, mic_open_params = {self.mic_open_params}")
        self.capture_end = False
        voice_source_file = self.tivo_ruc_dlg.getCaptureByFile()
        self.condition = threading.Condition()
        c = threading.Timer(0.001, self.consumePCM)
        p = None
        if voice_source_file:
            p = threading.Timer(0.001, self.producePCMByFile)
        else:
            p = threading.Timer(0.001, self.producePCMByCapture)

        if c != None and p != None:
            c.start()
            p.start()
