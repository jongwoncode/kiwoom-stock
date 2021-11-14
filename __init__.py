##__init__ 실행할 때 Ui 그리고 kiwoom이 연달아. 실행되게 만든다. 연쇄 반응처럼 실행되게 만든다.
from ui.ui import*

class Main():
    def __init__(self):
        print("실행할 메인 클래스")

        Ui_class()

## 해당 파일(__main__) 부분에서만 실행되게 보여주는 용도, 이게 메인 실행 파일이다 라는 것을 명시하기 위해 사용.
if __name__=="__main__":
    Main()
