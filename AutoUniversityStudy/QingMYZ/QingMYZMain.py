from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
import json
import random
import os

from AutoUniversityStudy.QingMYZ import *

class QingMYZClass():
    def __init__(self, user_data_file) -> None:
        # 必须参数
        self.__user_data_file = user_data_file
        self.__login_key = []
        self.__api_key = {}
        self.__aim_questions_num_total = 0
        self.__questions_num_now = 0
        self.__questions_num_day_max = 0
        self.__course_name = ''
        # 可选参数
        self.__min_question_time = 5 #秒
        self.__low_right_rate = 0.65
        self.__top_right_rate = 1.00

        self.__now_all_questions = 0
        self.finish = False

        # 初始化
        self.__getUserData()

    def del__(self):
        self.__updataUserData()

        return self.finish

    
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
                                                 self.__login_key[0])
                break
            except Exception as e:
                try_times += 1
                if try_times > 1:
                    print('登入失败')
                    raise e
                
        # 进入答题页面
        try_times = 0 # 异常后再次尝试次数
        while True:
            try:
                into_answer_web(driver, self.__course_name)
                break
            except Exception as e:
                try_times += 1
                if try_times > 1:
                    print('进入答题页面失败')
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
                    if now_all_questions + self.__questions_num_now >= self.__aim_questions_num_total:
                        print('已到达全部题目数目')
                        self.finish = True
                        break

                    print('-------------------------------')
                    # 记录开始时间
                    start_time = time.time()

                    # 获取当前题目
                    question = get_question(driver)

                    # 判断是否出现刷题检测
                    if detect_error(question):
                        driver.refresh()
                        continue

                    # 控制正确率
                    if self.__low_right_rate == 1:
                        answer = get_answer_by_all_right(question, self.__course_name)
                        if answer == []:
                            driver.refresh()
                            continue
                    else:
                        if now_all_questions > 20:
                            if now_right_rate > self.__low_right_rate:
                                if (right_question+1) / (now_all_questions+1) > self.__top_right_rate :
                                    answer = [random.choice(question[2])]
                                    print(f"\n正确率过高警告, 随机选择答案{answer}\n")
                                else:
                                    answer = get_answer_by_all(question, self.__api_key, self.__course_name)
                            else:
                                print("\n正确率过低警告!!!!!!!!!!!!!!!!!!\n")
                                # 查找答案
                                answer = get_answer_by_all(question, self.__api_key, self.__course_name)
                        else:
                            # 查找答案
                            answer = get_answer_by_all(question, self.__api_key, self.__course_name)

                    if answer == []:
                        driver.refresh()
                        continue

                    # 点击答案
                    right_answer, answer_sucess = click_answer(driver, answer, question[0], question)

                    # 答题后
                    after_answer(question, right_answer, self.__course_name)

                    # 记录结束时间
                    end_time = time.time()

                    # 统计及绘制数据
                    # 打印题目
                    print(f'题目:{question[0]} {question[1]}')
                    print('选项:', question[2])

                    # 打印答案是否正确
                    now_all_questions += 1
                    self.__now_all_questions += 1
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
                        print(f'补偿做题时间:{self.__min_question_time - (end_time - start_time):.2f}')
                        sleep(self.__min_question_time - (end_time - start_time))

                    # 输出统计时间
                    all_time += end_time - start_time
                    print(f'已经答题{all_time:.2f}s, 本题用时{end_time - start_time:.2f}s')

                    sleep(1)

                    if self.__now_all_questions >= self.__questions_num_day_max:
                        print('单轮答题数量上限')
                        driver.quit()
                        self.__now_all_questions = 0
                        break
                break
            except Exception as e:
                try_times += 1
                if try_times > 10:
                    self.__updataUserData()
                    raise e
                driver.refresh()

        # 更新用户数据
        self.__questions_num_now += self.__now_all_questions
    
    # 创建浏览器控制驱动
    def __createDriver(self):
        # 当前所在绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 返回上一级目录
        current_dir = os.path.dirname(current_dir)
        current_dir = os.path.dirname(current_dir)

        # 配置浏览器选项
        options = webdriver.ChromeOptions()

        # 设置chrome浏览器路径
        options.binary_location = f"{current_dir}\\ChromeWithDriver\\chrome.exe"

        # 设置无头浏览器
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        
        # 忽略浏览器控制警告
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # 设置随机生成UA
        ua = get_ua()
        options.add_argument('user-agent=' + ua)

        # 设置chromedriver路径
        service = Service(f"{current_dir}\\ChromeWithDriver\\chromedriver112.exe")

        # 创建浏览器
        driver = webdriver.Chrome(service=service, options=options)

        # 设置最长刷新等待时间
        driver.implicitly_wait(10)

        # 最大化窗口
        driver.maximize_window()

        return driver

    # 获取用户数据
    def __getUserData(self):
        # 读取用户数据文件
        with open(self.__user_data_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        # 读取用户登入数据
        if user_data['user']['verify_request'] != '':
            self.__login_key.append(user_data['user']['verify_request'])
        elif user_data['user']['account'] != '' and user_data['user']['password'] != '':
            self.__login_key.append(user_data['user']['account'])
            self.__login_key.append(user_data['user']['password'])
        else:
            raise ValueError('用户数据不完整')
        # 读取api_key数据
        if user_data['API_key']['Gemini'] != '':
            self.__api_key['Gemini'] = user_data['API_key']['Gemini']
        if user_data['API_key']['ChatGPT'] != '':
            self.__api_key['ChatGPT'] = user_data['API_key']['Gemini']
        if user_data['API_key']['NewBing'] != '':
            self.__api_key['NewBing'] = user_data['API_key']['Gemini']
        # 读取做题数据
        if user_data['answer_setting']['aim_questions_num_total'] != '':
            self.__aim_questions_num_total = user_data['answer_setting']['aim_questions_num_total']
            self.__aim_questions_num_total = int(self.__aim_questions_num_total)
        else:
            raise ValueError('答题设置数据不完整')
        if user_data['answer_setting']['questions_num_day_max'] != '':
            self.__questions_num_day_max = user_data['answer_setting']['questions_num_day_max']
            self.__questions_num_day_max = int(self.__questions_num_day_max)
        else:
            raise ValueError('答题设置数据不完整')
        if user_data['answer_setting']['course_name'] != '':
            self.__course_name = user_data['answer_setting']['course_name']
        else:
            raise ValueError('答题设置数据不完整')
        if user_data['now']['questions_num_now'] != '':
            self.__questions_num_now = user_data['now']['questions_num_now']
            self.__questions_num_now = int(self.__questions_num_now)
        else:
            self.__questions_num_now = 0
        if user_data['answer_setting']['low_right_rate'] != '':
            self.__low_right_rate = user_data['answer_setting']['low_right_rate']
            self.__low_right_rate = float(self.__low_right_rate)
        if user_data['answer_setting']['top_right_rate'] != '':
            self.__top_right_rate = user_data['answer_setting']['top_right_rate']
            self.__top_right_rate = float(self.__top_right_rate)
        if user_data['answer_setting']['min_question_time'] != '':
            self.__min_question_time = user_data['answer_setting']['min_question_time']
            self.__min_question_time = float(self.__min_question_time)
        if user_data['other']['now_all_questions'] != '':
            self.__now_all_questions = user_data['other']['now_all_questions']
            self.__now_all_questions = int(self.__now_all_questions)
                
    # 更新用户数据
    def __updataUserData(self):
        with open(self.__user_data_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
    
        with open(self.__user_data_file, 'w', encoding='utf-8') as f:
            user_data['now']['questions_num_now'] = self.__questions_num_now - self.__now_all_questions
            user_data['other']['now_all_questions'] = self.__now_all_questions
            json.dump(user_data, f, separators=(',', ':'), ensure_ascii=False)