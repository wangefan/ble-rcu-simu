from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog
from tivo_rcu_ui import Ui_TivoRcuDlg
from key_event_name import *
import os

import time
import threading

class TivoRcuDlg(QtWidgets.QDialog):
    def __init__(self, key_event_listener, capture_keyboard_listener):
        super(TivoRcuDlg, self).__init__()
        self.key_event_listener = key_event_listener
        self.capture_keyboard_listener = capture_keyboard_listener
        current_dir = os.getcwd()
        self.path_to_8k_file = os.path.join(
            current_dir, "./audio/find_spiderman_8k.wav")
        self.path_to_16k_file = os.path.join(
            current_dir, "./audio/find_spiderman_16k.wav")
        self.ui = Ui_TivoRcuDlg()
        self.ui.setupUi(self)
        self.setup_control()

    def get_8k_file_path(self):
        return self.path_to_8k_file
    
    def get_16k_file_path(self):
        return self.path_to_16k_file

    def setup_control(self):
        self.ui.mPower.clicked.connect(self.powerClicked)
        self.ui.mDPadLeft.pressed.connect(self.dpadLeftPressed)
        self.ui.mDPadLeft.released.connect(self.dpadLeftReleased)
        self.ui.mDPadRight.pressed.connect(self.dpadRightPressed)
        self.ui.mDPadRight.released.connect(self.dpadRightReleased)
        self.ui.mDPadUp.pressed.connect(self.dpadUpPressed)
        self.ui.mDPadUp.released.connect(self.dpadUpReleased)
        self.ui.mDPadDown.pressed.connect(self.dpadDownPressed)
        self.ui.mDPadDown.released.connect(self.dpadDownReleased)
        self.ui.mDPadOk.clicked.connect(self.dpadOkClicked)
        self.ui.mBack.clicked.connect(self.backClicked)
        self.ui.mVolUp.pressed.connect(self.dpadVolUpPressed)
        self.ui.mVolUp.released.connect(self.dpadVolUpReleased)
        self.ui.mVolDown.pressed.connect(self.dpadVolDownPressed)
        self.ui.mVolDown.released.connect(self.dpadVolDownReleased)
        self.ui.mTivo.clicked.connect(self.tivoClicked)
        self.ui.mVoice.clicked.connect(self.voiceClicked)
        self.ui.mCkbCaptureKeyboard.stateChanged.connect(
            self.captureKeyboardClicked)
        self.ui.mNum0.clicked.connect(self.num0Clicked)
        self.ui.mNum1.clicked.connect(self.num1Clicked)
        self.ui.mNum2.clicked.connect(self.num2Clicked)
        self.ui.mNum3.clicked.connect(self.num3Clicked)
        self.ui.mNum4.clicked.connect(self.num4Clicked)
        self.ui.mNum5.clicked.connect(self.num5Clicked)
        self.ui.mNum6.clicked.connect(self.num6Clicked)
        self.ui.mNum7.clicked.connect(self.num7Clicked)
        self.ui.mNum8.clicked.connect(self.num8Clicked)
        self.ui.mNum9.clicked.connect(self.num9Clicked)
        self.ui.mBtnOpen8k.clicked.connect(self.open8kClicked)
        self.ui.mBtnOpen16k.clicked.connect(self.open16kClicked)
        self.ui.mLbPathTo8k.setText(os.path.basename(self.path_to_8k_file))
        self.ui.mLbPathTo16k.setText(os.path.basename(self.path_to_16k_file))

    def setupThread(self, key_event_name):
        if self.key_event_listener != None:
            self.thread = threading.Thread(target=self.sendKey, args=(key_event_name,))
            self.thread.start()

    def sendKey(self, key_event_name):
        self.pressed = True
        while self.pressed:
            self.key_event_listener(key_event_name)
            self.key_event_listener(KEY_EVENT_NAME_RELEASE)
            if key_event_name == KEY_EVENT_NAME_VOLUP or key_event_name == KEY_EVENT_NAME_VOLDW:
                time.sleep(0.15)
            else:
                time.sleep(0.5)

    def destroyThread(self):
        self.pressed = False
        self.thread.join()

    def dpadLeftPressed(self):
        self.setupThread(KEY_EVENT_NAME_LEFT)

    def dpadLeftReleased(self):
        self.destroyThread()

    def dpadRightPressed(self):
        self.setupThread(KEY_EVENT_NAME_RIGHT)

    def dpadRightReleased(self):
        self.destroyThread()

    def dpadUpPressed(self):
        self.setupThread(KEY_EVENT_NAME_UP)

    def dpadUpReleased(self):
        self.destroyThread()

    def dpadDownPressed(self):
        self.setupThread(KEY_EVENT_NAME_DOWN)

    def dpadDownReleased(self):
        self.destroyThread()

    def dpadVolUpPressed(self):
        self.setupThread(KEY_EVENT_NAME_VOLUP)

    def dpadVolUpReleased(self):
        self.destroyThread()

    def dpadVolDownPressed(self):
        self.setupThread(KEY_EVENT_NAME_VOLDW)

    def dpadVolDownReleased(self):
        self.destroyThread()

    def powerClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_POWER)

    def dpadOkClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_SEL)

    def backClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_BACK)

    def tivoClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_TIVO)

    def voiceClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_VOICE)

    def captureKeyboardClicked(self):
        bCaptureKeyboard = self.ui.mCkbCaptureKeyboard.isChecked()
        if self.capture_keyboard_listener != None:
            self.capture_keyboard_listener(bCaptureKeyboard)

    def num0Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_0)

    def num1Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_1)

    def num2Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_2)

    def num3Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_3)

    def num4Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_4)

    def num5Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_5)

    def num6Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_6)

    def num7Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_7)

    def num8Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_8)

    def num9Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_9)

    def open8kClicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open 8k File", self.path_to_8k_file, "WAV Files (*.wav)")
        if file_path != "":
            self.path_to_8k_file = file_path
            self.ui.mLbPathTo8k.setText(os.path.basename(self.path_to_8k_file))

    def open16kClicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open 16k File", self.path_to_16k_file, "WAV Files (*.wav)")
        if file_path != "":
            self.path_to_16k_file = file_path
            self.ui.mLbPathTo16k.setText(os.path.basename(self.path_to_16k_file))
