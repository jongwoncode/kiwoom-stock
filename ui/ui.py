from kiwoom.kiwoom import *

import sys
from PyQt5.QtWidgets import *

class Ui_class():
    def __init__(self):
        print("Ui_class 입니다")

        self.app = QApplication(sys.argv)              ## UI를 실행하기 위해서 함수나 변수(sys.argv)들의 초기값을 잡아준다.

        self.kiwoom = Kiwoom()

        self.app.exec_()                                ## event loop를 실행시켜서, 프로그램이 종료되지 않게 만들어준다.