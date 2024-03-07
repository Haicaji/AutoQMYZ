from AutoUniversityStudy.QingMYZ import *

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
import random

class QingMYZClass():
    def __init__(self, user_data_file) -> None:
        # 必须参数
        self.__user_data_file = user_data_file
        self.__login_key = []
        self.__api_key = []
        self.__aim_questions_num_total = 0
        self.__questions_num_now = 0
        self.__questions_num_day_max = 0
        # 可选参数
        self.__course_name = []
        self.__min_question_time = 5
        self.__low_right_rate = 0.65
        self.__top_right_rate = 1.00

        # 初始化
        self.__getUserData()

    def del__(self):
        self.__updataUserData()
    
    # 主流程
    def mainProcess(self):
        # 获取浏览器控制驱动
        try_times = 0
        while True:
            try:
                driver = self.__createDriver()
                break
            except Exception as e:
                try_times += 1
                if try_times > 1:
                    print('创建浏览器控制驱动失败')
                    raise e

        # 登入
        try_times = 0 # 异常后再次尝试次数
        while True:
            try:
                if len(self.__login_key) > 1:
                    # 账号密码登入
                    login_user_by_code(driver, 
                                       self.__login_key[0], self.__login_key[1])
                else:
                    # verify_request登入
                    login_user_by_verify_request(driver, 
                                                 self.__login_key)
                break
            except Exception as e:
                try_times += 1
                if try_times > 1:
                    print('登入或进入答题页面失败')
                    raise e

        # 当轮数据
        now_all_questions = 0 # 当轮总题数
        right_question = 0 # 当轮正确总题数
        all_time = 0 # 当轮总时间

        # 作答(防止特殊情况异常中断)
        try_times = 0
        while True:
            try:
                # ---------答题环节----------
                while True:
                    print('-------------------------------')
                    # 记录开始时间
                    start_time = time()

                    # 获取当前题目
                    question = get_question(driver)

                    # 判断是否出现刷题检测
                    if detect_error(question):
                        driver.refresh()

                    # 控制正确率
                    if now_all_questions > 20:
                        if now_right_rate > self.__low_right_rate:
                            if (right_question+1) / (now_all_questions+1) > self.__top_right_rate :
                                answer = [random.choice(question[2])]
                                print(f"\n正确率过高警告, 随机选择答案{answer}\n")
                        else:
                            print("\n正确率过低警告!!!!!!!!!!!!!!!!!!\n")
                            # 查找答案
                            answer = get_answer_by_all(question)
                    else:
                        # 查找答案
                        answer = get_answer_by_all(question)

                    # 点击答案
                    right_answer, answer_sucess = click_answer(driver, answer, question[0])

                    # 答题后
                    after_answer(question, right_answer)

                    # 记录结束时间
                    end_time = time()

                    # 统计及绘制数据
                    # 打印题目
                    print(f'题目:{question[0]} {question[1]}')
                    print('选项:', question[2])

                    # 打印答案是否正确
                    now_all_questions += 1
                    if answer_sucess:
                        right_question += 1
                        print('回答正确')
                    else:
                        if right_answer == answer:
                            print('回答超时, 正确答案: ', right_answer)
                        else:
                            print('回答错误, 正确答案: ', right_answer)

                    # 当前回答数据
                    now_right_rate = right_question/now_all_questions
                    print(f"正确题数:{right_question}, 错误题数:{now_all_questions-right_question}")
                    print(f"总题目:{now_all_questions}, 正确率:{now_right_rate*100:.2f}%")

                    # 休眠一下
                    if self.__min_question_time > end_time - start_time:
                        sleep(self.__min_question_time - (end_time - start_time))

                    # 输出统计时间
                    all_time += end_time - start_time
                    print(f'已经答题{all_time:.2f}s, 本题用时{end_time - start_time:.2f}s')

                    sleep(1)

                    if now_all_questions >= self.__questions_num_day_max:
                        driver.quit()
                        break
                # -------------------------------
                break
            except Exception as e:
                try_times += 1
                if try_times > 1:
                    raise e
    
    # 创建浏览器控制驱动
    def __createDriver(self):
        # 配置浏览器选项
        options = webdriver.ChromeOptions()

        # 设置chrome浏览器路径
        options.binary_location = r"./chrome/chrome.exe"

        # # 设置用户UA
        # user_agent = r"Mozilla/5.0 (Linux; Android 13; Redmi K40 Build/SKQ1.201006.003; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/112.0.5615.48 Mobile Safari/537.36;webank/h5face;webank/1.0 yiban_android/5.1.2"
        # options.add_argument(f"--user-agent={user_agent}")

        # 设置chromedriver路径
        service = Service(r"./chrome/chromedriver112.exe")

        # 创建浏览器
        driver = webdriver.Chrome(service=service, options=options)

        # 设置最长刷新等待时间
        driver.implicitly_wait(10)

        # 最大化窗口
        driver.maximize_window()

        return driver

    # 获取用户数据
    def __getUserData(self):
        print(self.__user_data_file)

    # 更新用户数据
    def __updataUserData(self):
        pass