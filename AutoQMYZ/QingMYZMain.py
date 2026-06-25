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
        self.__tasks = []
        self.__UA = ''
        self.__verify_request = ''
        self.finish = False # 是否已经完成
        self.driver = None # 暴露当前的浏览器驱动，用于外部终止任务
        self.stopped = False # 外部终止标志

        # 初始化
        self.__getUserData()

    def _sleep(self, seconds):
        start = time.time()
        while time.time() - start < seconds:
            if getattr(self, 'stopped', False):
                raise InterruptedError("Task stopped manually")
            time.sleep(0.1)

    def del__(self):
        self.__updataUserData()
        
        # 只有当所有的课程都完成时，整个用户配置才算完成
        all_finished = True
        for task in self.__tasks:
            if not task.get('finish', False):
                all_finished = False
                break
        self.finish = all_finished
        return self.finish

    # 主流程
    def mainProcess(self):
        # 每次运行前重新加载数据，防止多进程/多实例并发冲突
        self.__getUserData()

        # 遍历处理该用户的所有未完成课程
        for index, task in enumerate(self.__tasks):
            if task.get('finish', False):
                continue

            print(f"\n================ 开始处理课程: {task['course_name']} ================")
            try:
                self.__run_single_course(index)
            except Exception as e:
                print(f"处理课程 {task['course_name']} 时发生异常: {e}")
                # 即使某一门课失败，也继续处理下一门课，或者选择向上传播异常
                raise e

    # 运行单个特定任务
    def run_single_task_by_name(self, course_name):
        self.__getUserData()
        for index, task in enumerate(self.__tasks):
            if task['course_name'] == course_name:
                if task.get('finish', False):
                    print(f"课程 {course_name} 已完成，无需运行。")
                    return
                print(f"\n================ 开始处理课程: {task['course_name']} ================")
                try:
                    self.__run_single_course(index)
                except Exception as e:
                    print(f"处理课程 {task['course_name']} 时发生异常: {e}")
                    raise e
                return
        raise ValueError(f"未找到课程: {course_name}")

    # 运行单个课程的答题流程
    def __run_single_course(self, course_index):
        task = self.__tasks[course_index]

        # 获取浏览器控制驱动
        try_times = 0 # 异常后再次尝试次数
        while True: 
            if getattr(self, 'stopped', False):
                raise InterruptedError("Task stopped manually")
            try:
                driver, self.__UA = self.__createDriver(self.__UA)
                self.driver = driver # 记录驱动实例以供外部中断
                self.__updataUserData() # 及时保存更新后的 UA
                break
            except Exception as e:
                if getattr(self, 'stopped', False):
                    raise e
                try_times += 1
                if try_times > 1:
                    print('创建浏览器控制驱动失败')
                    raise e

        try:
            # 登入
            try_times = 0 # 异常后再次尝试次数
            while True:
                if getattr(self, 'stopped', False):
                    raise InterruptedError("Task stopped manually")
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
                    if getattr(self, 'stopped', False):
                        raise e
                    try_times += 1
                    if try_times > 1:
                        print('登入失败')
                        raise e
                    
            # 进入答题页面
            try_times = 0 # 异常后再次尝试次数
            while True:
                if getattr(self, 'stopped', False):
                    raise InterruptedError("Task stopped manually")
                try:
                    into_answer_web(driver, task['course_name'])
                    break
                except Exception as e:
                    if getattr(self, 'stopped', False):
                        raise e
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
            aim_questions_num_total = int(task['aim_questions_num_total'])

            low_right_rate = float(task.get('low_right_rate', 0.7))
            top_right_rate = float(task.get('top_right_rate', 0.9))
            min_question_time = float(task.get('min_question_time', 8.0))

            current_question_num = int(task.get('current_question_num', 0))
            current_right_num = int(task.get('current_right_num', 0))

            course_finish = False

            # 作答(防止特殊情况异常中断)
            try_times = 0
            try_times_max = 30
            while True:
                if getattr(self, 'stopped', False):
                    raise InterruptedError("Task stopped manually")
                try:
                    # ---------答题环节----------
                    while True:
                        if getattr(self, 'stopped', False):
                            raise InterruptedError("Task stopped manually")
                        if current_question_num >= aim_questions_num_total:
                            print(f"{task['course_name']}: 已到达全部题目数目")
                            task['finish'] = True
                            self.__updataUserData()
                            course_finish = True
                            break

                        print('-------------------------------')
                        # 记录开始时间
                        start_time = time.time()
                        self._sleep(0.5)
                        # 获取当前题目
                        question = get_question(driver)

                        # 打印题目与选项
                        print(f'题目:{question[0]} {question[1]}')
                        print('选项:', question[2])

                        # 判断是否出现刷题检测
                        if detect_error(question):
                            driver.refresh()
                            robot_detected_time += 1
                            continue

                        # 控制正确率
                        if low_right_rate == 1:
                            answer = get_answer_by_all_right(question, task['course_name'])
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
                                        answer = get_answer_by_all(question, task['course_name'], driver)
                                else:
                                    print("\n正确率过低警告!!!!!!!!!!!!!!!!!!\n")
                                    # 查找答案
                                    answer = get_answer_by_all(question, task['course_name'], driver)
                            else:
                                # 查找答案
                                answer = get_answer_by_all(question, task['course_name'], driver)

                        # 点击答案
                        right_answer, answer_sucess = click_answer(driver, answer, question[0], question)

                        # 答题后
                        after_answer(question, right_answer, task['course_name'])

                        # 记录结束时间
                        end_time = time.time()

                        # 打印答案是否正确
                        now_all_questions += 1 # 当前轮数做的题数,不包括中断前,主要用于计算正确率
                        current_question_num += 1
                        if answer_sucess:
                            right_question += 1
                            current_right_num += 1
                            print('回答正确')
                        else:
                            if right_answer == answer:
                                print('回答超时, 正确答案: ', right_answer)
                            else:
                                print('回答错误, 正确答案: ', right_answer)

                        # 答完一题立即更新本地记录
                        task['current_question_num'] = current_question_num
                        task['current_right_num'] = current_right_num

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
                            self._sleep(sleep_time)

                        # 输出统计时间
                        all_time += end_time - start_time
                        print(f'已经答题{all_time:.2f}s, 本题用时{end_time - start_time:.2f}s, 总共用时{(end_time - start_time)+sleep_time:.2f}s')
                        print(f"其他信息: trytime:{try_times}, RobotDetectedtime:{robot_detected_time}")

                        self._sleep(1)

                        if current_question_num >= aim_questions_num_total:
                            print(f"{task['course_name']}: 已到达全部题目数目")
                            task['finish'] = True
                            self.__updataUserData()
                            course_finish = True
                            break
                        
                        self.__updataUserData()
                    break
                except Exception as e:
                    if getattr(self, 'stopped', False):
                        raise e
                    try_times += 1
                    if try_times > try_times_max:
                        # 异常中断时保存当前做题进度
                        task['current_question_num'] = current_question_num
                        task['current_right_num'] = current_right_num
                        self.__updataUserData()
                        raise e
                    driver.refresh()

            # 同步更新本门课程的最终数据
            if course_finish:
                task['finish'] = True
            else:
                task['current_question_num'] = current_question_num
                task['current_right_num'] = current_right_num
                task['finish'] = False

            self.__updataUserData()

        finally:
            # 确保浏览器驱动总能退出
            try:
                driver.quit()
            except:
                pass

    # 创建浏览器控制驱动
    def __createDriver(self, UA):
        current_dir = get_project_root()

        # 配置浏览器选项
        options = webdriver.ChromeOptions()

        # 设置chrome浏览器路径
        options.binary_location = os.path.join(current_dir, "ChromeWithDriver", "chrome.exe")

        # 根据配置决定是否以最小化启动（配合之后的隐藏/显示控制）
        if not getattr(self, 'show_browser_gui', False):
            options.add_argument('--start-minimized')
        
        # 忽略浏览器控制警告
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # 设置随机生成UA
        if UA != "":
            ua = UA
        else:
            ua = get_ua()
        options.add_argument('user-agent=' + ua + ";webank/h5face;webank/1.0 yiban_android/5.0.17")

        # 设置chromedriver路径
        service = Service(os.path.join(current_dir, "ChromeWithDriver", "chromedriver112.exe"))

        # 创建浏览器
        driver = webdriver.Chrome(service=service, options=options)
        apply_stealth_script(driver, current_dir)

        # 设置最长刷新等待时间
        driver.implicitly_wait(10)

        # 最大化窗口 (只有初始显示时才最大化，避免最小化启动被撤销)
        if getattr(self, 'show_browser_gui', False):
            driver.maximize_window()

        # 在创建浏览器后定位 HWND 并进行初始隐藏控制
        try:
            import ctypes
            unique_title = f"AutoQMYZ_Task_{getattr(self, 'task_id', 'unknown')}_{random.randint(10000, 99999)}"
            driver.execute_script(f"document.title = '{unique_title}'")
            sleep(0.2)
            
            hwnd = [0]
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            
            def EnumWindowsCallback(h, extra):
                length = ctypes.windll.user32.GetWindowTextLengthW(h)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(h, buffer, length + 1)
                    title = buffer.value
                    if unique_title in title:
                        hwnd[0] = h
                        return False
                return True
                
            ctypes.windll.user32.EnumWindows(WNDENUMPROC(EnumWindowsCallback), 0)
            if hwnd[0] != 0:
                self.hwnd = hwnd[0]
                print(f"[Driver] Found window HWND: {self.hwnd}")
                if not getattr(self, 'show_browser_gui', False):
                    self.hide_browser()
            else:
                print("[Driver] Failed to find window HWND by title.")
        except Exception as e:
            print(f"[Driver] Error setting window title or finding HWND: {e}")

        return driver, ua

    def hide_browser(self):
        hwnd = getattr(self, 'hwnd', None)
        if hwnd:
            try:
                import ctypes
                # SW_HIDE = 0
                ctypes.windll.user32.ShowWindow(hwnd, 0)
                print(f"[Driver] Browser window {hwnd} hidden.")
            except Exception as e:
                print(f"[Driver] Error hiding browser window: {e}")

    def show_browser(self):
        hwnd = getattr(self, 'hwnd', None)
        if hwnd:
            try:
                import ctypes
                # SW_RESTORE = 9, SW_SHOW = 5
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.ShowWindow(hwnd, 5)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                print(f"[Driver] Browser window {hwnd} shown.")
            except Exception as e:
                print(f"[Driver] Error showing browser window: {e}")

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
        self.__tasks = user_data.get('tasks', user_data.get('courses', []))
        self.__UA = user_data.get('other', {}).get('UA', '')
                
    # 更新用户数据
    def __updataUserData(self):
        with open(self.__user_data_file, 'r', encoding='utf-8-sig') as f:
            user_data = json.load(f)
    
        with open(self.__user_data_file, 'w', encoding='utf-8') as f:
            if self.__verify_request != '':
                user_data['user']['verify_request'] = self.__verify_request
                
            if 'courses' in user_data:
                del user_data['courses']
            user_data['tasks'] = self.__tasks

            if 'other' not in user_data:
                user_data['other'] = {}

            if self.__UA != "":
                user_data['other']['UA'] = self.__UA

            json.dump(user_data, f, separators=(',', ':'), ensure_ascii=False)
