from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog
from tivo_rcu_ui import Ui_TivoRcuDlg
from key_event_name import *
import os

from threading import Timer
import time


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
        self.ui.mRdCaptureFile.clicked.connect(self.captureFileClicked)
        self.ui.mRdCaptureVoice.clicked.connect(self.captureVoiceClicked)
        self.setCaptureByFile(True)

    def detectEvent(self, key_event_name, key_event_name_release=None):
        if key_event_name_release is None:
            if self.timer_started:
                self.key_event_listener(key_event_name)
        else:
            self.timer_started = False
            self.key_event_listener(key_event_name)
            self.key_event_listener(KEY_EVENT_NAME_RELEASE)

    def dpadLeftPressed(self):
        self.timer_started = True
        t = Timer(0.5, self.detectEvent, args=(KEY_EVENT_NAME_LEFT,))
        t.start()

    def dpadLeftReleased(self):
        self.detectEvent(KEY_EVENT_NAME_LEFT, KEY_EVENT_NAME_RELEASE,)

    def dpadRightPressed(self):
        self.timer_started = True
        t = Timer(0.5, self.detectEvent, args=(KEY_EVENT_NAME_RIGHT,))
        t.start()

    def dpadRightReleased(self):
        self.detectEvent(KEY_EVENT_NAME_RIGHT, KEY_EVENT_NAME_RELEASE,)

    def dpadUpPressed(self):
        self.timer_started = True
        t = Timer(0.5, self.detectEvent, args=(KEY_EVENT_NAME_UP,))
        t.start()

    def dpadUpReleased(self):
        self.detectEvent(KEY_EVENT_NAME_UP, KEY_EVENT_NAME_RELEASE,)

    def dpadDownPressed(self):
        self.timer_started = True
        t = Timer(0.5, self.detectEvent, args=(KEY_EVENT_NAME_DOWN,))
        t.start()

    def dpadDownReleased(self):
        self.detectEvent(KEY_EVENT_NAME_DOWN, KEY_EVENT_NAME_RELEASE,)

    def dpadVolUpPressed(self):
        self.timer_started = True
        t = Timer(0.15, self.detectEvent, args=(KEY_EVENT_NAME_VOLUP,))
        t.start()

    def dpadVolUpReleased(self):
        self.detectEvent(KEY_EVENT_NAME_VOLUP, KEY_EVENT_NAME_RELEASE,)

    def dpadVolDownPressed(self):
        self.timer_started = True
        t = Timer(0.15, self.detectEvent, args=(KEY_EVENT_NAME_VOLDW,))
        t.start()

    def dpadVolDownReleased(self):
        self.detectEvent(KEY_EVENT_NAME_VOLDW, KEY_EVENT_NAME_RELEASE,)

    def powerClicked(self):
        self.detectEvent(KEY_EVENT_NAME_POWER, KEY_EVENT_NAME_RELEASE,)

    def dpadOkClicked(self):
        self.detectEvent(KEY_EVENT_NAME_SEL, KEY_EVENT_NAME_RELEASE,)

    def backClicked(self):
        self.detectEvent(KEY_EVENT_NAME_BACK, KEY_EVENT_NAME_RELEASE,)

    def tivoClicked(self):
        self.detectEvent(KEY_EVENT_NAME_TIVO, KEY_EVENT_NAME_RELEASE,)

    def voiceClicked(self):
        self.detectEvent(KEY_EVENT_NAME_VOICE, KEY_EVENT_NAME_RELEASE,)

    def captureKeyboardClicked(self):
        bCaptureKeyboard = self.ui.mCkbCaptureKeyboard.isChecked()
        if self.capture_keyboard_listener != None:
            self.capture_keyboard_listener(bCaptureKeyboard)

    def num0Clicked(self):
        self.detectEvent(KEY_EVENT_NAME_0, KEY_EVENT_NAME_RELEASE,)

    def num1Clicked(self):
        self.detectEvent(KEY_EVENT_NAME_1, KEY_EVENT_NAME_RELEASE,)

    def num2Clicked(self):
        self.detectEvent(KEY_EVENT_NAME_2, KEY_EVENT_NAME_RELEASE,)

    def num3Clicked(self):
        self.detectEvent(KEY_EVENT_NAME_3, KEY_EVENT_NAME_RELEASE,)

    def num4Clicked(self):
        self.detectEvent(KEY_EVENT_NAME_4, KEY_EVENT_NAME_RELEASE,)

    def num5Clicked(self):
        self.detectEvent(KEY_EVENT_NAME_5, KEY_EVENT_NAME_RELEASE,)

    def num6Clicked(self):
        self.detectEvent(KEY_EVENT_NAME_6, KEY_EVENT_NAME_RELEASE,)

    def num7Clicked(self):
        self.detectEvent(KEY_EVENT_NAME_7, KEY_EVENT_NAME_RELEASE,)

    def num8Clicked(self):
        self.detectEvent(KEY_EVENT_NAME_8, KEY_EVENT_NAME_RELEASE,)

    def num9Clicked(self):
        self.detectEvent(KEY_EVENT_NAME_9, KEY_EVENT_NAME_RELEASE,)

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
            self.ui.mLbPathTo16k.setText(
                os.path.basename(self.path_to_16k_file))

    def captureFileClicked(self):
        self.setCaptureByFile(True)

    def captureVoiceClicked(self):
        self.setCaptureByFile(False)

    def setCaptureByFile(self, capture_by_file):
        self.ui.mRdCaptureFile.setChecked(capture_by_file)
        self.ui.mRdCaptureVoice.setChecked(not capture_by_file)
        if capture_by_file:
            self.ui.groupBox.setEnabled(True)
            self.ui.groupBox_2.setEnabled(True)
            self.ui.mBtnOpen16k.setEnabled(True)
            self.ui.mBtnOpen8k.setEnabled(True)
            self.ui.mLbPathTo8k.setEnabled(True)
            self.ui.mLbPathTo16k.setEnabled(True)
        else:
            self.ui.groupBox.setEnabled(False)
            self.ui.groupBox_2.setEnabled(False)
            self.ui.mBtnOpen16k.setEnabled(False)
            self.ui.mBtnOpen8k.setEnabled(False)
            self.ui.mLbPathTo8k.setEnabled(False)
            self.ui.mLbPathTo16k.setEnabled(False)

    def getCaptureByFile(self):
        return self.ui.mRdCaptureFile.isChecked()
