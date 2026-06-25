from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
import json
import random
import os
from time import sleep

from AutoQMYZ import *

class QingMYZClass():
    def __init__(self, user_data_file) -> None:
        # 必须参数
        self.__user_data_file = user_data_file
        self.__login_key = []
        self.__courses = []
        self.__UA = ''
        self.__verify_request = ''
        self.finish = False # 是否已经完成

        # 初始化
        self.__getUserData()

    def del__(self):
        self.__updataUserData()
        
        # 只有当所有的课程都完成时，整个用户配置才算完成
        all_finished = True
        for course in self.__courses:
            if not course.get('finish', False):
                all_finished = False
                break
        self.finish = all_finished
        return self.finish

    # 主流程
    def mainProcess(self):
        # 每次运行前重新加载数据，防止多进程/多实例并发冲突
        self.__getUserData()

        # 遍历处理该用户的所有未完成课程
        for index, course in enumerate(self.__courses):
            if course.get('finish', False):
                continue

            print(f"\n================ 开始处理课程: {course['course_name']} ================")
            try:
                self.__run_single_course(index)
            except Exception as e:
                print(f"处理课程 {course['course_name']} 时发生异常: {e}")
                # 即使某一门课失败，也继续处理下一门课，或者选择向上传播异常
                raise e

    # 运行单个课程的答题流程
    def __run_single_course(self, course_index):
        course = self.__courses[course_index]

        # 获取浏览器控制驱动
        try_times = 0 # 异常后再次尝试次数
        while True: 
            try:
                driver, self.__UA = self.__createDriver(self.__UA)
                self.__updataUserData() # 及时保存更新后的 UA
                break
            except Exception as e:
                try_times += 1
                if try_times > 1:
                    print('创建浏览器控制驱动失败')
                    raise e

        try:
            # 登入
            try_times = 0 # 异常后再次尝试次数
            while True:
                try:
                    if len(self.__login_key) > 1:
                        # 账号密码登入
                        self.__verify_request, self.__UA = login_user_by_code(
                            driver, self.__login_key[0], self.__login_key[1], self.__UA
                        )
                    else:
                        # verify_request登入
                        login_user_by_verify_request(driver, self.__login_key[0])
                    
                    self.__updataUserData() # 及时保存更新后的 verify_request 与 UA
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
                    into_answer_web(driver, course['course_name'])
                    break
                except Exception as e:
                    try_times += 1
                    if try_times > 1:
                        print('进入答题页面失败')
                        raise e

            # 当轮数据
            now_all_questions = 0 # 当轮已做的题数
            right_question = 0 # 当轮正确的题数
            all_time = 0 # 当轮已用时
            robot_detected_time = 0

            # 从配置中解析当前课程的各项参数
            aim_questions_num_total = int(course['aim_questions_num_total'])
            questions_num_day_max = int(course['questions_num_day_max'])
            # 增加随机范围
            questions_num_day_max += random.randint(0, 10)

            low_right_rate = float(course.get('low_right_rate', 0.65))
            top_right_rate = float(course.get('top_right_rate', 1.00))
            min_question_time = float(course.get('min_question_time', 5.0))

            questions_all_num_now = int(course.get('questions_all_num_now', 0))
            last_time_question_num = int(course.get('last_time_question_num', 0))

            course_finish = False

            # 作答(防止特殊情况异常中断)
            try_times = 0
            try_times_max = 30
            while True:
                try:
                    # ---------答题环节----------
                    while True:
                        if questions_all_num_now + last_time_question_num >= aim_questions_num_total:
                            print(f"{course['course_name']}: 已到达全部题目数目")
                            last_time_question_num = 0
                            course_finish = True
                            break

                        print('-------------------------------')
                        # 记录开始时间
                        start_time = time.time()
                        sleep(0.5)
                        # 获取当前题目
                        question = get_question(driver)

                        # 判断是否出现刷题检测
                        if detect_error(question):
                            driver.refresh()
                            robot_detected_time += 1
                            continue

                        # 控制正确率
                        if low_right_rate == 1:
                            answer = get_answer_by_all_right(question, course['course_name'])
                            if answer == []:
                                driver.refresh()
                                continue
                        else:
                            if now_all_questions > 20:
                                now_right_rate = right_question / now_all_questions
                                if now_right_rate > low_right_rate:
                                    # 随机生成一个最高正确率
                                    top_right_rate_random = random.uniform(top_right_rate - 0.05, top_right_rate + 0.05)
                                    if (right_question+1) / (now_all_questions+1) > top_right_rate_random:
                                        answer = [random.choice(question[2])]
                                        print(f"\n正确率过高警告, 随机选择答案{answer}\n")
                                    else:
                                        answer = get_answer_by_all(question, course['course_name'])
                                else:
                                    print("\n正确率过低警告!!!!!!!!!!!!!!!!!!\n")
                                    # 查找答案
                                    answer = get_answer_by_all(question, course['course_name'])
                            else:
                                # 查找答案
                                answer = get_answer_by_all(question, course['course_name'])

                        # 点击答案
                        right_answer, answer_sucess = click_answer(driver, answer, question[0], question)

                        # 答题后
                        after_answer(question, right_answer, course['course_name'])

                        # 记录结束时间
                        end_time = time.time()

                        # 统计及绘制数据
                        # 打印题目
                        print(f'题目:{question[0]} {question[1]}')
                        print('选项:', question[2])

                        # 打印答案是否正确
                        now_all_questions += 1 # 当前轮数做的题数,不包括中断前,主要用于计算正确率
                        last_time_question_num += 1
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

                        # 休眠以防被检测
                        sleep_time = 0.0
                        if min_question_time > end_time - start_time:
                            if min_question_time - (end_time - start_time) > 2:
                                sleep_time = random.uniform(min_question_time - (end_time - start_time) - 2, 
                                                            min_question_time - (end_time - start_time) + 2)
                            else:
                                sleep_time = random.uniform(min_question_time - (end_time - start_time), 
                                                            min_question_time - (end_time - start_time) + 2)
                            sleep_time = round(sleep_time, 2)
                            print(f'补偿做题时间:{sleep_time:.2f}')      
                            sleep(sleep_time)

                        # 输出统计时间
                        all_time += end_time - start_time
                        print(f'已经答题{all_time:.2f}s, 本题用时{end_time - start_time:.2f}s, 总共用时{(end_time - start_time)+sleep_time:.2f}s')
                        print(f"其他信息: trytime:{try_times}, RobotDetectedtime:{robot_detected_time}")

                        sleep(1)

                        if last_time_question_num >= questions_num_day_max:
                            print(f"{course['course_name']}: 单轮答题数量上限")
                            if last_time_question_num + questions_all_num_now >= aim_questions_num_total:
                                print(f"{course['course_name']}: 已到达全部题目数目")
                                course_finish = True
                            break
                    break
                except Exception as e:
                    try_times += 1
                    if try_times > try_times_max:
                        # 异常中断时保存当前做题进度
                        course['questions_all_num_now'] = questions_all_num_now + last_time_question_num
                        course['last_time_question_num'] = last_time_question_num
                        self.__updataUserData()
                        raise e
                    driver.refresh()

            # 同步更新本门课程的最终数据
            if course_finish:
                course['questions_all_num_now'] = 0
                course['last_time_question_num'] = 0
                course['finish'] = True
            else:
                course['questions_all_num_now'] = questions_all_num_now + last_time_question_num
                course['last_time_question_num'] = last_time_question_num
                course['finish'] = False

            self.__updataUserData()

        finally:
            # 确保浏览器驱动总能退出
            try:
                driver.quit()
            except:
                pass

    # 创建浏览器控制驱动
    def __createDriver(self, UA):
        # 当前所在绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 返回上一级目录(AutoQMYZ/ -> 项目根目录)
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
        if UA != "":
            ua = UA
        else:
            ua = get_ua()
        options.add_argument('user-agent=' + ua + ";webank/h5face;webank/1.0 yiban_android/5.0.17")

        # 设置chromedriver路径
        service = Service(f"{current_dir}\\ChromeWithDriver\\chromedriver112.exe")

        # 创建浏览器
        driver = webdriver.Chrome(service=service, options=options)

        # 设置最长刷新等待时间
        driver.implicitly_wait(10)

        # 最大化窗口
        driver.maximize_window()

        return driver, ua

    # 获取用户数据
    def __getUserData(self):
        # 读取用户数据文件
        with open(self.__user_data_file, 'r', encoding='utf-8-sig') as f:
            user_data = json.load(f)
        
        # 读取用户登入数据
        self.__login_key = []
        if user_data['user']['verify_request'] != '':
            self.__login_key.append(user_data['user']['verify_request'])
        elif user_data['user']['account'] != '' and user_data['user']['password'] != '':
            self.__login_key.append(user_data['user']['account'])
            self.__login_key.append(user_data['user']['password'])
        else:
            raise ValueError('用户数据不完整')

        # 读取做题课程数据与 UA
        self.__courses = user_data.get('courses', [])
        self.__UA = user_data.get('other', {}).get('UA', '')
                
    # 更新用户数据
    def __updataUserData(self):
        with open(self.__user_data_file, 'r', encoding='utf-8-sig') as f:
            user_data = json.load(f)
    
        with open(self.__user_data_file, 'w', encoding='utf-8') as f:
            if self.__verify_request != '':
                user_data['user']['verify_request'] = self.__verify_request
                
            user_data['courses'] = self.__courses

            if 'other' not in user_data:
                user_data['other'] = {}

            if self.__UA != "":
                user_data['other']['UA'] = self.__UA

            json.dump(user_data, f, separators=(',', ':'), ensure_ascii=False)
