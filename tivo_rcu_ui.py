# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tivo_rcu.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_TivoRcuDlg(object):
    def setupUi(self, TivoRcuDlg):
        TivoRcuDlg.setObjectName("TivoRcuDlg")
        TivoRcuDlg.resize(389, 660)
        self.mDPadRight = QtWidgets.QPushButton(TivoRcuDlg)
        self.mDPadRight.setGeometry(QtCore.QRect(180, 70, 31, 31))
        self.mDPadRight.setAutoRepeatDelay(306)
        self.mDPadRight.setObjectName("mDPadRight")
        self.mDPadLeft = QtWidgets.QPushButton(TivoRcuDlg)
        self.mDPadLeft.setGeometry(QtCore.QRect(80, 70, 31, 31))
        self.mDPadLeft.setAutoRepeatDelay(306)
        self.mDPadLeft.setObjectName("mDPadLeft")
        self.mDPadUp = QtWidgets.QPushButton(TivoRcuDlg)
        self.mDPadUp.setGeometry(QtCore.QRect(130, 20, 31, 31))
        self.mDPadUp.setAutoRepeatDelay(306)
        self.mDPadUp.setObjectName("mDPadUp")
        self.mDPadDown = QtWidgets.QPushButton(TivoRcuDlg)
        self.mDPadDown.setGeometry(QtCore.QRect(130, 120, 31, 31))
        self.mDPadDown.setAutoRepeatDelay(306)
        self.mDPadDown.setObjectName("mDPadDown")
        self.mDPadOk = QtWidgets.QPushButton(TivoRcuDlg)
        self.mDPadOk.setGeometry(QtCore.QRect(130, 70, 31, 31))
        self.mDPadOk.setAutoRepeatDelay(306)
        self.mDPadOk.setObjectName("mDPadOk")
        self.mNum1 = QtWidgets.QPushButton(TivoRcuDlg)
        self.mNum1.setGeometry(QtCore.QRect(110, 410, 41, 41))
        self.mNum1.setAutoRepeatDelay(306)
        self.mNum1.setObjectName("mNum1")
        self.mNum2 = QtWidgets.QPushButton(TivoRcuDlg)
        self.mNum2.setGeometry(QtCore.QRect(170, 410, 41, 41))
        self.mNum2.setAutoRepeatDelay(306)
        self.mNum2.setObjectName("mNum2")
        self.mNum3 = QtWidgets.QPushButton(TivoRcuDlg)
        self.mNum3.setGeometry(QtCore.QRect(230, 410, 41, 41))
        self.mNum3.setAutoRepeatDelay(306)
        self.mNum3.setObjectName("mNum3")
        self.mNum6 = QtWidgets.QPushButton(TivoRcuDlg)
        self.mNum6.setGeometry(QtCore.QRect(230, 460, 41, 41))
        self.mNum6.setAutoRepeatDelay(306)
        self.mNum6.setObjectName("mNum6")
        self.mNum4 = QtWidgets.QPushButton(TivoRcuDlg)
        self.mNum4.setGeometry(QtCore.QRect(110, 460, 41, 41))
        self.mNum4.setAutoRepeatDelay(306)
        self.mNum4.setObjectName("mNum4")
        self.mNum5 = QtWidgets.QPushButton(TivoRcuDlg)
        self.mNum5.setGeometry(QtCore.QRect(170, 460, 41, 41))
        self.mNum5.setAutoRepeatDelay(306)
        self.mNum5.setObjectName("mNum5")
        self.mNum9 = QtWidgets.QPushButton(TivoRcuDlg)
        self.mNum9.setGeometry(QtCore.QRect(230, 510, 41, 41))
        self.mNum9.setAutoRepeatDelay(306)
        self.mNum9.setObjectName("mNum9")
        self.mNum7 = QtWidgets.QPushButton(TivoRcuDlg)
        self.mNum7.setGeometry(QtCore.QRect(110, 510, 41, 41))
        self.mNum7.setAutoRepeatDelay(306)
        self.mNum7.setObjectName("mNum7")
        self.mNum8 = QtWidgets.QPushButton(TivoRcuDlg)
        self.mNum8.setGeometry(QtCore.QRect(170, 510, 41, 41))
        self.mNum8.setAutoRepeatDelay(306)
        self.mNum8.setObjectName("mNum8")
        self.mNum0 = QtWidgets.QPushButton(TivoRcuDlg)
        self.mNum0.setGeometry(QtCore.QRect(170, 560, 41, 41))
        self.mNum0.setAutoRepeatDelay(306)
        self.mNum0.setObjectName("mNum0")
        self.mBack = QtWidgets.QPushButton(TivoRcuDlg)
        self.mBack.setGeometry(QtCore.QRect(80, 130, 31, 31))
        self.mBack.setAutoRepeatDelay(306)
        self.mBack.setObjectName("mBack")
        self.mVolDown = QtWidgets.QPushButton(TivoRcuDlg)
        self.mVolDown.setGeometry(QtCore.QRect(20, 110, 31, 51))
        self.mVolDown.setAutoRepeatDelay(306)
        self.mVolDown.setObjectName("mVolDown")
        self.mVolUp = QtWidgets.QPushButton(TivoRcuDlg)
        self.mVolUp.setGeometry(QtCore.QRect(20, 50, 31, 51))
        self.mVolUp.setAutoRepeatDelay(306)
        self.mVolUp.setObjectName("mVolUp")
        self.mChanDown = QtWidgets.QPushButton(TivoRcuDlg)
        self.mChanDown.setGeometry(QtCore.QRect(240, 110, 31, 51))
        self.mChanDown.setAutoRepeatDelay(306)
        self.mChanDown.setObjectName("mChanDown")
        self.mChanUp = QtWidgets.QPushButton(TivoRcuDlg)
        self.mChanUp.setGeometry(QtCore.QRect(240, 40, 31, 51))
        self.mChanUp.setAutoRepeatDelay(306)
        self.mChanUp.setObjectName("mChanUp")
        self.mTivo = QtWidgets.QPushButton(TivoRcuDlg)
        self.mTivo.setGeometry(QtCore.QRect(120, 160, 41, 41))
        self.mTivo.setAutoRepeatDelay(306)
        self.mTivo.setObjectName("mTivo")
        self.mPower = QtWidgets.QPushButton(TivoRcuDlg)
        self.mPower.setGeometry(QtCore.QRect(20, 10, 31, 31))
        self.mPower.setIconSize(QtCore.QSize(12, 12))
        self.mPower.setAutoRepeatDelay(306)
        self.mPower.setObjectName("mPower")
        self.info = QtWidgets.QLabel(TivoRcuDlg)
        self.info.setGeometry(QtCore.QRect(90, 630, 231, 20))
        font = QtGui.QFont()
        font.setBold(True)
        self.info.setFont(font)
        self.info.setObjectName("info")
        self.mVoice = QtWidgets.QPushButton(TivoRcuDlg)
        self.mVoice.setGeometry(QtCore.QRect(180, 160, 51, 41))
        self.mVoice.setAutoRepeatDelay(306)
        self.mVoice.setObjectName("mVoice")
        self.mCkbCaptureKeyboard = QtWidgets.QCheckBox(TivoRcuDlg)
        self.mCkbCaptureKeyboard.setGeometry(QtCore.QRect(110, 600, 151, 23))
        self.mCkbCaptureKeyboard.setObjectName("mCkbCaptureKeyboard")
        self.mLbPathTo8k = QtWidgets.QLabel(TivoRcuDlg)
        self.mLbPathTo8k.setGeometry(QtCore.QRect(100, 290, 251, 31))
        self.mLbPathTo8k.setObjectName("mLbPathTo8k")
        self.mLbPathTo16k = QtWidgets.QLabel(TivoRcuDlg)
        self.mLbPathTo16k.setGeometry(QtCore.QRect(100, 360, 261, 31))
        self.mLbPathTo16k.setObjectName("mLbPathTo16k")
        self.groupBox = QtWidgets.QGroupBox(TivoRcuDlg)
        self.groupBox.setGeometry(QtCore.QRect(40, 260, 331, 71))
        self.groupBox.setObjectName("groupBox")
        self.mBtnOpen8k = QtWidgets.QPushButton(self.groupBox)
        self.mBtnOpen8k.setGeometry(QtCore.QRect(10, 30, 41, 31))
        self.mBtnOpen8k.setObjectName("mBtnOpen8k")
        self.groupBox_2 = QtWidgets.QGroupBox(TivoRcuDlg)
        self.groupBox_2.setGeometry(QtCore.QRect(40, 330, 331, 71))
        self.groupBox_2.setObjectName("groupBox_2")
        self.mBtnOpen16k = QtWidgets.QPushButton(self.groupBox_2)
        self.mBtnOpen16k.setGeometry(QtCore.QRect(10, 30, 41, 31))
        self.mBtnOpen16k.setObjectName("mBtnOpen16k")
        self.mRdCaptureVoice = QtWidgets.QRadioButton(TivoRcuDlg)
        self.mRdCaptureVoice.setGeometry(QtCore.QRect(20, 200, 141, 23))
        self.mRdCaptureVoice.setObjectName("mRdCaptureVoice")
        self.mRdCaptureFile = QtWidgets.QRadioButton(TivoRcuDlg)
        self.mRdCaptureFile.setGeometry(QtCore.QRect(20, 230, 121, 23))
        self.mRdCaptureFile.setObjectName("mRdCaptureFile")
        self.groupBox_2.raise_()
        self.groupBox.raise_()
        self.mDPadRight.raise_()
        self.mDPadLeft.raise_()
        self.mDPadUp.raise_()
        self.mDPadDown.raise_()
        self.mDPadOk.raise_()
        self.mNum1.raise_()
        self.mNum2.raise_()
        self.mNum3.raise_()
        self.mNum6.raise_()
        self.mNum4.raise_()
        self.mNum5.raise_()
        self.mNum9.raise_()
        self.mNum7.raise_()
        self.mNum8.raise_()
        self.mNum0.raise_()
        self.mBack.raise_()
        self.mVolDown.raise_()
        self.mVolUp.raise_()
        self.mChanDown.raise_()
        self.mChanUp.raise_()
        self.mTivo.raise_()
        self.mPower.raise_()
        self.info.raise_()
        self.mVoice.raise_()
        self.mCkbCaptureKeyboard.raise_()
        self.mLbPathTo8k.raise_()
        self.mLbPathTo16k.raise_()
        self.mRdCaptureVoice.raise_()
        self.mRdCaptureFile.raise_()

        self.retranslateUi(TivoRcuDlg)
        QtCore.QMetaObject.connectSlotsByName(TivoRcuDlg)

    def retranslateUi(self, TivoRcuDlg):
        _translate = QtCore.QCoreApplication.translate
        TivoRcuDlg.setWindowTitle(_translate("TivoRcuDlg", "Tivo RCU"))
        self.mDPadRight.setText(_translate("TivoRcuDlg", "→"))
        self.mDPadLeft.setText(_translate("TivoRcuDlg", "←"))
        self.mDPadUp.setText(_translate("TivoRcuDlg", "↑"))
        self.mDPadDown.setText(_translate("TivoRcuDlg", "↓"))
        self.mDPadOk.setText(_translate("TivoRcuDlg", "Ok"))
        self.mNum1.setText(_translate("TivoRcuDlg", "1"))
        self.mNum2.setText(_translate("TivoRcuDlg", "2"))
        self.mNum3.setText(_translate("TivoRcuDlg", "3"))
        self.mNum6.setText(_translate("TivoRcuDlg", "6"))
        self.mNum4.setText(_translate("TivoRcuDlg", "4"))
        self.mNum5.setText(_translate("TivoRcuDlg", "5"))
        self.mNum9.setText(_translate("TivoRcuDlg", "9"))
        self.mNum7.setText(_translate("TivoRcuDlg", "7"))
        self.mNum8.setText(_translate("TivoRcuDlg", "8"))
        self.mNum0.setText(_translate("TivoRcuDlg", "0"))
        self.mBack.setText(_translate("TivoRcuDlg", "↺"))
        self.mVolDown.setText(_translate("TivoRcuDlg", "↓vol"))
        self.mVolUp.setText(_translate("TivoRcuDlg", "↑vol"))
        self.mChanDown.setText(_translate("TivoRcuDlg", "↓ch"))
        self.mChanUp.setText(_translate("TivoRcuDlg", "↑ch"))
        self.mTivo.setText(_translate("TivoRcuDlg", "Tivo"))
        self.mPower.setText(_translate("TivoRcuDlg", "P"))
        self.info.setText(_translate("TivoRcuDlg", "Press keyboard \"Esc\" to exit .."))
        self.mVoice.setText(_translate("TivoRcuDlg", "Voice"))
        self.mCkbCaptureKeyboard.setText(_translate("TivoRcuDlg", "Capture Keyboard"))
        self.mLbPathTo8k.setText(_translate("TivoRcuDlg", "path to 8k"))
        self.mLbPathTo16k.setText(_translate("TivoRcuDlg", "path to 16k"))
        self.groupBox.setTitle(_translate("TivoRcuDlg", "specify 8K file"))
        self.mBtnOpen8k.setText(_translate("TivoRcuDlg", "open"))
        self.groupBox_2.setTitle(_translate("TivoRcuDlg", "spcify 16k file"))
        self.mBtnOpen16k.setText(_translate("TivoRcuDlg", "open"))
        self.mRdCaptureVoice.setText(_translate("TivoRcuDlg", "Capture by voice"))
        self.mRdCaptureFile.setText(_translate("TivoRcuDlg", "Capture by file"))
