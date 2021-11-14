## OCX 방식의 컴포넌트 방식으로 설치가 됐다.
    # 응용프로그램에서 키움 Open API를 실행할 수 있게 한 거다! -> 제어가 가능하다.
    # 이걸 파이썬에서 제어가 가능하게 끔 만들어줘야 한다. ->PyQt5.QAxContainer

import os

from PyQt5.QAxContainer import*
from PyQt5.QtCore import*
from config.errorCode import *
from PyQt5.QtTest import *
from config.kiwoomType import *


class Kiwoom(QAxWidget):            ## QAxWidget 상속시키겠다.
    def __init__(self):
        super().__init__()              ## 부모의 __init__을 실행시키겠다.

        print("Kiwoom 클래스 입니다.")

        self.realType = RealType()

        #___________________Screen Number 모음___________________#
        self.screen_my_info = "2000"
        self.screen_calculation_stock = "4000"
        self.screen_real_stock = "5000" #(32_3) 종목별로 할당한 스크린번호
        self.screen_meme_stock = "6000" #(32_3) 종목별 할당할 주문용 스크린 번호.
        self.screen_start_stop_real = "1000"

        #_____________________eventloop 모음______________________#
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()
        self.calculator_event_loop = QEventLoop()

        #_______________________변수 모음______________________________#
        self.account_num = None
        self.account_stock_dict = {}        #(17_1) 계좌 변수 모음
        self.not_account_stock_dict = {}    #(20_1) 미체결 요청 정보 저장.
        self.portfolio_stock_dict = {}      #(31_1) 종목 dict형태로 저장.

        #______________________계좌 관련 변수___________________________#
        self.use_money = 0
        self.use_money_percent = 0.5

        #_____________________종목분석용_______________________________#
        self.calcul_data = []

        ################################################################
        self.get_ocx_instance()
        self.event_slots()
        self.real_event_slots()


        self.signal_login_commConnect()
        self.get_account_info()                     ## (5) 로그인하고 실행되게 끔 __init__에 넣어준다.
        self.detail_account_info()                  ## (6) 예수금 가져오는 것 아래서 만듬
        self.detail_account_mystock()               ## 계좌평가 잔고 내역 요청
        self.not_concluded_account()                ## (20) 미체결요청

        self.read_code()                            ##(29) 저장된 종목들 불러온다.
        self.screen_number_setting()                ##(32) 종목들중 스크린번호가 중복되지 않게 조정해주는 함수의 실행

        ## (33_3) 실시간등록 함수 SetRealReg(), [KOA_개발가이드_조건검색_관련함수_SetRealReg()] -> # realdata에 event와 slot을 걸고, signal을 보내줘야한다.
        # -> # 이걸 받으려면 시간을 정해줘야 한다. (장중, 장외) [그걸 바로 아래서 할 거다.]
        # FID번호 = [KOA_실시간목록_장시작시간]                     # 0은 처음등록할 때 하는 것이다. 나머지 실시간으로 볼게 있다면 1로 바꿔서 추가등록을 해야한다. 그때도 0으로하면 초기화된다.
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, "", self.realType.REALTYPE["장시작시간"]["장운영구분"], "0")

        for code in self.portfolio_stock_dict.keys():
            screen_num = self.portfolio_stock_dict[code]["스크린번호"]
            # [KOA_실시간목록_주식체결_체결시간(관련 다 나옴)]
            fids = self.realType.REALTYPE["주식체결"]["체결시간"]
            # 추가등록이니까 1로 해준다.
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")
            print("실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s" % (code, screen_num, fids))


    def get_ocx_instance(self):             ## 응용 프로그램을 제어할 수 있게 해준다. 이걸 등록함 으로서 Kiwoom open API를 사용할 수 있게 된다.
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")


    def event_slots(self):                               ## 이벤트를 담아두는 함수
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)      ##(8)TR data event로 걸고, 정보를 self.trdata_slot으로 받는다.


    def real_event_slots(self):                        ##(33) 실시간데이터처리!! 이벤트 걸기.
        self.OnReceiveRealData.connect(self.realdata_slot)      ##(33_1) 슬롯(self.realdata_slot)을 만들어준다. 아래로!! 아래서 슬롯 걸기.


    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")                              ## 네트워크, 서버 응용 프로그램에 데이터를 전송하게끔 만들어주는 함수.

        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()               ##(1) 로그인 완료 전까지 다음이 실행이 안됨

    def login_slot(self, errCode):
        print(errCode)                              ## errCode가 0 이어야 로그인에 성공
        print(errors(errCode))                      ##(3) 로그인하고 결과 출력

        self.login_event_loop.exit()                ##(2) 로그인 완료되면 event_loop를 빠져나옴.

#(4) 내 계좌정보 가져오기
    def get_account_info(self):
        account_list = self.dynamicCall("GetLoginInfo(String)", "ACCNO")           #KOA Studio에서 가져온다.

        self.account_num = account_list.split(";")[0]                 ## 계좌가 "12132312;12313123:" 이런식으로 나온다.
        print("나의 보유 계좌번호 %s" % self.account_num)                     ##(4) 계좌번호는 많이 쓰기때문에 self로 넣어준다.

#(7) 예수금 가져오기, 이런거 가져오려면 키움에 TR 요청을 해야한다.
## (10) 계좌번호만 적으면 뭘 원하는지 모를 수 있다.[ Open API 조회 함수를 호출해서 전문을 서버로 전송합니다.]
## (11) "예수금상세현황요청"은 내가 지정한 단어이다. 내 마음대로 "예수금상세" 이렇게 불러와도 된다. 다만, 예수금상세현황요청의 key값 "opw00001"만 잘 써주면 된다.
# (12) ("내가 지은 요청이름", "TR번호", "preNext", "화면번호")
    # (13) screen_number
    # 앞으로 TR요청을 할 때마다 screen_number를 기입한다. screen_number는 데이터를 그룹핑해준다.
    def detail_account_info(self):
        print("예수금 요청하는 부분")

        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num) #(9) TR data에 받을 데이터 입력
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "예수금상세현황요청", "opw00001", "0", self.screen_my_info)
            #(15) 코드가 받아오기 전까지 block 처리해줘야 한다. [QEventLoop]
        self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop.exec_()


    def detail_account_mystock(self, sPrevNext="0"):
        print("계좌평가 잔고내역 요청하기 연속조회 %s" % sPrevNext)

        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "계좌평가잔고내역요청", "opw00018", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

## (19) 미체결종목 요청_[KOA_TR_미체결요철_멀티데이터]
    def not_concluded_account(self, sPrevNext="0"):
        print("미체결요청")

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("SetInputValue(QString, QString, int, QString)", "실시간미체결요청", "opt10075", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()


##(14) TR 데이터를 받는 곳!!  ## 앞으로 모든 TR요청은 여기서 받는다. [KOA_개발가이드_조회와실시간데이터처리_관련함수]
    ##(14_1) 보유종목수가 20개가 넘으면 sPreNext = 2 로 요청한다.
    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        '''
        tr요청을 받는 구역이다! 슬롯이다!
        :param sScrNo: 스크린번호
        :param sRQName: 내가 요청했을 때 지은 이름
        :param sTrCode: 요청id, tr코드
        :param sRecordName: 사용 안함
        :param sPrevNext: 다음 페이지가 있는지
        :return:
        '''
        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "예수금")    #(15) KOA에서 꺼내오는 방식
            print("예수금 %s" % int(deposit))

            self.use_money = int(deposit) * self.use_money_percent              ## 5억 * 0.5 =2억 5천
            self.use_money = self.use_money / 4                                 ## 2억 5천 / 4 => 한종목 살때 이정도 사는 것.


            ok_deposit = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "출금가능금액")
            print("출금가능금액 %s" % int(ok_deposit))
            # (15-1) 정보 받아오고 나면, QEventLoop 탈출
            self.detail_account_info_event_loop.exit()


        if sRQName == "계좌평가잔고내역요청":
            ## 0이면 첫번째 종목, 1이면 두번째 종목
            total_buy_money = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총매입금액")
            total_buy_money_result = int(total_buy_money)
            print("총매입금액 %s" % total_buy_money_result)

            total_profit_loss_rate = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총수익률(%)")
            total_profit_loss_rate_result =float(total_profit_loss_rate)
            print("총수익률(%%) %s" % total_profit_loss_rate_result)


            ##(16) 계좌에 있는 종목 가져오기, 먼저 종목이 몇개인지 count해줘야 한다.
            ##(16_1) GetReatCnt는 한번에 20개까지만 출력가능하다.
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            cnt = 0
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                code = code.strip()[1:]

                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량")
                buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가")
                learn_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")
                total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액")
                possible_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량")

                ##(17) 위 데이터들은 자주 사용하므로, 계산하기 편하게 dict형태로 변환한다.(__init__으로 이동해서 변수들을 모아놓자)
                if code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict.update({code:{}})

                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(possible_quantity.strip())


                self.account_stock_dict[code].update({"종목명": code_nm})
                self.account_stock_dict[code].update({"보유수량": stock_quantity})
                self.account_stock_dict[code].update({"매입가": buy_price})
                self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                self.account_stock_dict[code].update({"현재가": current_price})
                self.account_stock_dict[code].update({"매입금액": total_chegual_price})
                self.account_stock_dict[code].update({"매매가능수량": possible_quantity})

                cnt += 1

            print("보유 종목수 %s" % cnt)
            print("계좌 종목 내역 %s" % self.account_stock_dict)

            ##(16_2) 보유종목 21번째부터 다음페이지로 넘어가라는 Signal줘야 한다. 다음페이지 없으면, sPrevNext = "0" or ""
            if sPrevNext == "2":
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.detail_account_info_event_loop.exit()


            self.detail_account_info_event_loop.exit()

        elif sRQName == "실시간미체결요청":

            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)

            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                order_no = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문상태") # 접수, 확인, 체결
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문가격")
                order_gubun = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문구분")  # -매도, +매수
                not_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "미체결수량")
                ok_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "체결량")

                code = code.strip()
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip("+").lstrip("-")
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())

                if order_no in self.not_account_stock_dict:
                    pass
                else:
                    self.not_account_stock_dict[order_no] = {}


                self.not_account_stock_dict[order_no].update({"종목코드": code})
                self.not_account_stock_dict[order_no].update({"종목명": code_nm})
                self.not_account_stock_dict[order_no].update({"주문번호": order_no})
                self.not_account_stock_dict[order_no].update({"주문상태": order_status})
                self.not_account_stock_dict[order_no].update({"주문수량": order_quantity})
                self.not_account_stock_dict[order_no].update({"주문가격": order_price})
                self.not_account_stock_dict[order_no].update({"주문구분": order_gubun})
                self.not_account_stock_dict[order_no].update({"미체결수량": not_quantity})
                self.not_account_stock_dict[order_no].update({"체결량": ok_quantity})

                print("미체결종목 : %s" % self.not_account_stock_dict[order_no])

            self.detail_account_info_event_loop.exit()

        if sRQName == "주식일봉차트조회":
            # [KOA_TR목록_주식일봉차트조회요청_싱글데이터]
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
            code = code.strip()                 ## 공백 제거
            print("%s 일봉데이터 요청" % code)     ##(25) 이게 안나오는 에러가 뜰거다.->QEventloop설정

            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            print("데이터 일수 %s" % cnt)

            # [주식일봉차트조회는 한번에 최대 600개까지만 받아옴]
            for i in range(cnt) :
                data = []

                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가") # 출력 : 00070
                value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래량")  # 출력 : 00070
                trading_value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래대금") # 출력 : 00070
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "일자")   # 출력 : 00070
                start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시가")   # 출력 : 00070
                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "고가")   # 출력 : 00070
                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "저가")   # 출력 : 00070

                # data = self.dynamicCall("GetCommDataEx(QString, QString)", sTrCode, sRQName)
                # [["", "현재가", "거래량", "거래대금", "일자", "시가", "고가", "저가", ""], ["", "현재가", "거래량", "거래대금", "일자", "시가", "고가", "저가", ""] ]
                # 이런식으로 나와서 이거 맞춰주려고 하는 것이다.
                data.append("")
                data.append(current_price.strip())
                data.append(value.strip())
                data.append(trading_value.strip())
                data.append(date.strip())
                data.append(start_price.strip())
                data.append(high_price.strip())
                data.append(low_price.strip())
                data.append("")

                self.calcul_data.append(data.copy())

            print(len(self.calcul_data))

            # [주식일봉차트조회는 한번에 최대 600개까지만 받아옴]
            if sPrevNext == "2":
                self.day_kiwoom_db(code = code, sPrevNext=sPrevNext)

            else :
                ##(27) 여기서 조건에 부합하는 종목 따로 저장하는 것이다.
                print("총 일수 %s" % len(self.calcul_data))

                pass_success = False
                #120일 이평성을 그릴만큼의 데이터가 있는지 체크
                if self.calcul_data == None or len(self.calcul_data) <120 :
                    pass_success = False

                else :
                    # 120일 이상 되면은

                    total_price = 0
                    for value in self.calcul_data[:120]:    # [오늘, 하루전, 2일전, 3일전 .... 119일전]
                        total_price += int(value[1])

                    moving_average_price = total_price / 120

                    # 오늘자 주가가 120일 이평선에 걸쳐있거나, 점프한지 확인,
                    bottom_stock_price = False
                    check_price = None
                    if (int(self.calcul_data[0][7]) <= moving_average_price and int(self.calcul_data[0][6]) >= moving_average_price) or \
                            (int(self.calcul_data[0][7]) >= moving_average_price and int(self.calcul_data[0][6]) >= moving_average_price) :
                        print("오늘 주가 120이평선에 걸쳐있는 것 확인")
                        bottom_stock_price = True
                        check_price = int(self.calcul_data[0][6])

                    # 과거 일봉들이 120일 이평선보다 밑에 있는지 확인.
                    # 그렇게 확인을 하다가 일봉이 120일 이평선보다 위에 있으면 계산 진행.

                    prev_price = None #(28_1) 과거의 일봉 저가
                    if bottom_stock_price == True:

                        moving_average_price_prev = 0
                        price_top_moving = False

                        idx = 1
                        while True :

                            if len(self.calcul_data[idx:]) < 120: # 120일치가 있는지 계속 확인
                                print("120일치가 없음!")
                                break

                            total_price = 0
                            for value in self.calcul_data[idx:120+idx]:
                                total_price +=int(value[1])
                            moving_average_price_prev = total_price / 120

                            if moving_average_price_prev <= int(self.calcul_data[idx][6]) and idx <= 20:
                                print("20일 동안 주가가 120일 이평선과 같거나 위에 있으면 조건 통과 못함")
                                price_top_moving = False
                                break

                            elif int(self.calcul_data[idx][7]) > moving_average_price_prev and idx >20:
                                print("120일 이평선 위에 있는 일봉 확인됨")
                                price_top_moving = True
                                prev_price = int(self.calcul_data[idx][7])  #(28) 과거의 일봉 저가
                                break

                            idx +=1

                        # 해당 부분 이평선이 가장 최근 일자의 이평선 가격보다 낮은지 확인한다.
                        if price_top_moving == True:
                            if moving_average_price > moving_average_price_prev and check_price > prev_price :
                                print("포착된 이평선의 가격이 오늘자(최근일자) 이평선 가격보다 낮은 것 확인됨")
                                print("포착된 부분의 일봉 저가가 오늘자 일봉의 고가보다 낮은지 확인됨")
                                pass_success =True


                if pass_success == True:
                    print("조건부 통과됨")

                    code_nm = self.dynamicCall("GetMasterCodeName(QString)", code)
                    f = open("files/condition_stock.txt", "a", encoding="utf8")
                    f.write("%s\t%s\t%s\n" % (code, code_nm, str(self.calcul_data[0][1])))
                    f.close()

                elif pass_success == False:
                    print("조건부 통과 못함")

                self.calcul_data.clear()        # list내의 데이터를 모두 지우겠다.
                self.calculator_event_loop.exit()       #(25)loop out!



# (21) 종목코드 받아오기! [KOA_개발가이드_기타함수_종목정보관련함수_GetCodeListByMarket() 함수]
    def get_code_list_by_market(self, market_code):
        '''
        종목 코드 받아오는 함수
        :param market_code: 코스피[0], 코스닥[10], ELW[3],ETF[8]
        :return: 종목 코드
        '''
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_code)
        code_list = code_list.split(";")[:-1]

        return code_list

# (22) 종목 분석시 실행용!!
    def calculator_fnc(self):
        '''
        종목 분석 실행용 함수[이걸로 실행할 것이다.]
        :return: code_list
        '''
        code_list = self.get_code_list_by_market("10")
        print("코스닥 갯수 %s" % len(code_list))

        for idx,code in enumerate(code_list):
            ##(23) 해당 스크린 번호를 부여하고[DisconnectRealData], 코드를 요청하는 것이다./ 다음 코드 요청할 때 다시 스크린 번호 부여하는 것.
            ##(23-1) 스크린번호를 한번이라도 요청하면 그룹이 만들어 진 것이므로, 끊어주는 건 개인의 선택이다.
            self.dynamicCall("DisconnectRealData(QString)", self.screen_calculation_stock)

            print("%s / %s : KOSDAG Stock Code : %s is updating..." % (idx+1, len(code_list), code))

            self.day_kiwoom_db(code=code)
            ##(24) 받는 부분은 slot으로 넘어간다.



# (20 일봉데이터 받아오기! -> 그랜빌 4법칙 [KOA_TR목록_주식일봉차트조회요청]
    def day_kiwoom_db(self, code=None, date=None, sPrevNext="0"):

        # (26) TR데이터를 빠르게 조회하다보면 error가 발생한다. 이를 해결하기위해서 시간텀을 줘야한다.
        QTest.qWait(3600)       # 3.6초 딜레이

        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")

        if date != None:
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)

        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", sPrevNext, self.screen_calculation_stock)

        self.calculator_event_loop.exec_()      #(25)번 에러로 인한 QEventLoop() 설정


    def read_code(self):

        if os.path.exists("files/condition_stock.txt"):            #(29) 있으면 True, 없으면 False
            f = open("files/condition_stock.txt", "r", encoding="utf8")

            lines = f.readlines()
            for line in lines:
                if line != "":
                    ls = line.split("\t")          # ["203923", "종목명", "현재가\n"]

                    stock_code = ls[0]
                    stock_name = ls[1]
                    stock_price = int(ls[2].split("\n")[0])
                    stock_price = abs(stock_price)              ##(30) 현재가가 하락이었으면 -가 붙어서 나온다. 이를 제거

                    #(31_1) 종목 dict형태로 저장./  # {"2090923" : {"종목명":"케이엠더블류","현재가" :2000}, "0090923":{"종목명":"삼성전자", "현재가" :86000}}
                    self.portfolio_stock_dict.update({stock_code:{"종목명":stock_name, "현재가":stock_price}})

            f.close()
            print(self.portfolio_stock_dict)

    #(32_1) 계좌평가잔고내역, 미체결종목, 포트폴리오 종목의 중복을 방지하는 함수
    def screen_number_setting(self):

        screen_overwrite = []

        # 계좌평가잔고내역에 있는 종목들
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        # 미체결에 있는 종목들
        for order_number in self.not_account_stock_dict.keys():
            code = self.not_account_stock_dict[order_number]["종목코드"]
            if code not in screen_overwrite:
                screen_overwrite.append(order_number)

        # 포트폴리오에 담겨 있는 종목들
        for code in self.portfolio_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        ##(32_2) 중복을 제거하고 screen_overite에 담았다면 다시 스크린번호를 할당.    #위에서 스크린번호 추가
        cnt = 0
        for code in screen_overwrite:

            temp_screen = int(self.screen_real_stock)
            meme_screen = int(self.screen_meme_stock)

            if (cnt % 50) ==0:          # 스크린번호 하나당 종목코드 50개씩 할당하겠다.
                temp_screen += 1
                self.screen_real_stock = str(temp_screen)

            if (cnt % 50) == 0:
                meme_screen +=1
                self.screen_meme_stock =str(meme_screen)

            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].update({"스크린번호": str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].update({"주문용스크린번호": str(self.screen_meme_stock)})

            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict.update({code: {"스크린번호": str(self.screen_real_stock), "주문용스크린번호": str(self.screen_meme_stock)}})

            cnt +=1

        print(self.portfolio_stock_dict)


    # (33_2) 실시간데이터처리 슬롯 [KOA_개발가이드_조회와실시간데이터처리_OnReceiveRealData()]
    def realdata_slot(self, sCode, sRealType, sRealData):
        '''
        실시간데이터받아오기
        :param sCode: 종목코드
        :param sRealType: 실시간타입
        :param sRealData: 실시간데이터전문(안쓴다)
        :return: 
        '''
        if sRealType == "장시작시간":
            fid = self.realType.REALTYPE[sRealType]["장운영구분"]
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)

            if value == "0":
                print("장 시작 전")

            elif value == "3":
                print("장 시작")

            elif value == "2":
                print("장 종료, 동시호가로 넘어감")

            elif value == "4":
                print("3시 30분 장 종료")

        elif sRealType == "주식체결":
            print(sCode)


