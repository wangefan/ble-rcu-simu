from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog
from key_detector import KeyDetector
from tivo_rcu.tivo_rcu_ui import Ui_TivoRcuDlg
import tivo_rcu.key_table_constants as ktc
import os

class TivoRcuDlg(QtWidgets.QDialog):
    def __init__(self, key_event_listener, capture_keyboard_listener, key_descriptor_obj):
        super(TivoRcuDlg, self).__init__()
        self.key_event_listener = key_event_listener
        self.capture_keyboard_listener = capture_keyboard_listener
        self.key_table_obj = key_descriptor_obj[ktc.KEY_TABLE]
        self.key_detector = KeyDetector(
            self.handlePress, self.handleRelease, self.handleClick)
        current_dir = os.getcwd()
        self.path_to_8k_file = os.path.join(
            current_dir, "./audio/find_spiderman_8k.wav")
        self.path_to_16k_file = os.path.join(
            current_dir, "./audio/find_spiderman_16k.wav")
        self.ui = Ui_TivoRcuDlg()
        self.ui.setupUi(self)
        self.setup_control()

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if e.key() == QtCore.Qt.Key_Escape:
            print(f'TivoRcuDlg.keyPressEvent, key esc pressed! prevent close dialog!')

    def get_8k_file_path(self):
        return self.path_to_8k_file

    def get_16k_file_path(self):
        return self.path_to_16k_file

    def setup_control(self):
        self.ui.KEY_POWER.pressed.connect(self.onRressed)
        self.ui.KEY_POWER.released.connect(self.onReleased)
        self.ui.KEY_LEFT.pressed.connect(self.onRressed)
        self.ui.KEY_LEFT.released.connect(self.onReleased)
        self.ui.KEY_RIGHT.pressed.connect(self.onRressed)
        self.ui.KEY_RIGHT.released.connect(self.onReleased)
        self.ui.KEY_UP.pressed.connect(self.onRressed)
        self.ui.KEY_UP.released.connect(self.onReleased)
        self.ui.KEY_DOWN.pressed.connect(self.onRressed)
        self.ui.KEY_DOWN.released.connect(self.onReleased)
        self.ui.KEY_SEL.pressed.connect(self.onRressed)
        self.ui.KEY_SEL.released.connect(self.onReleased)
        self.ui.KEY_BACK.pressed.connect(self.onRressed)
        self.ui.KEY_BACK.released.connect(self.onReleased)
        self.ui.KEY_VOLUP.pressed.connect(self.onRressed)
        self.ui.KEY_VOLUP.released.connect(self.onReleased)
        self.ui.KEY_VOLDW.pressed.connect(self.onRressed)
        self.ui.KEY_VOLDW.released.connect(self.onReleased)
        self.ui.KEY_TIVO.pressed.connect(self.onRressed)
        self.ui.KEY_TIVO.released.connect(self.onReleased)
        self.ui.KEY_VOICE.pressed.connect(self.onRressed)
        self.ui.KEY_VOICE.released.connect(self.onReleased)
        self.ui.mCkbCaptureKeyboard.stateChanged.connect(
            self.captureKeyboardClicked)
        self.ui.KEY_0.pressed.connect(self.onRressed)
        self.ui.KEY_0.released.connect(self.onReleased)
        self.ui.KEY_1.pressed.connect(self.onRressed)
        self.ui.KEY_1.released.connect(self.onReleased)
        self.ui.KEY_2.pressed.connect(self.onRressed)
        self.ui.KEY_2.released.connect(self.onReleased)
        self.ui.KEY_3.pressed.connect(self.onRressed)
        self.ui.KEY_3.released.connect(self.onReleased)
        self.ui.KEY_4.pressed.connect(self.onRressed)
        self.ui.KEY_4.released.connect(self.onReleased)
        self.ui.KEY_5.pressed.connect(self.onRressed)
        self.ui.KEY_5.released.connect(self.onReleased)
        self.ui.KEY_6.pressed.connect(self.onRressed)
        self.ui.KEY_6.released.connect(self.onReleased)
        self.ui.KEY_7.pressed.connect(self.onRressed)
        self.ui.KEY_7.released.connect(self.onReleased)
        self.ui.KEY_8.pressed.connect(self.onRressed)
        self.ui.KEY_8.released.connect(self.onReleased)
        self.ui.KEY_9.pressed.connect(self.onRressed)
        self.ui.KEY_9.released.connect(self.onReleased)
        self.ui.mBtnOpen8k.clicked.connect(self.open8kClicked)
        self.ui.mBtnOpen16k.clicked.connect(self.open16kClicked)
        self.ui.mLbPathTo8k.setText(os.path.basename(self.path_to_8k_file))
        self.ui.mLbPathTo16k.setText(os.path.basename(self.path_to_16k_file))
        self.ui.mRdCaptureFile.clicked.connect(self.captureFileClicked)
        self.ui.mRdCaptureVoice.clicked.connect(self.captureVoiceClicked)
        self.setCaptureByFile(True)

    def handlePress(self, key_name):
        print(f'handlePress, key_name = {key_name}')
        self.key_event_listener(key_name, True)

    def handleRelease(self, key_name):
        print(f'handleRelease, key_name = {key_name}')
        self.key_event_listener(key_name, False)

    def handleClick(self, key_name):
        print(f'handleClick, key_name = {key_name}')
        self.key_event_listener(key_name, True)
        self.key_event_listener(key_name, False)

    def onRressed(self):
        sender = self.sender()
        key_name = sender.objectName()
        print('onRressed, key_name = ' + sender.objectName())
        self.key_detector.onPressed(key_name)

    def onReleased(self):
        sender = self.sender()
        key_name = sender.objectName()
        print('onReleased, key_name = ' + sender.objectName())
        self.key_detector.onReleased(key_name)

    def captureKeyboardClicked(self):
        bCaptureKeyboard = self.ui.mCkbCaptureKeyboard.isChecked()
        if self.capture_keyboard_listener != None:
            self.capture_keyboard_listener(bCaptureKeyboard)

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
