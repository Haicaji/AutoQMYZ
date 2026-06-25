# 获取答案
import json
import pandas as pd
import requests
import time
import re
import msvcrt
import sys
import random

from os.path import exists, abspath, dirname
from time import sleep

from AutoQMYZ.GetAnswerProcessing.AIConfig import load_ai_config, load_answer_config

# 全局人工作答状态暂存器 (task_id -> question_info)
manual_questions = {}

# 当前所在绝对路径
current_dir = dirname(abspath(__file__))
# 返回上一级目录(GetAnswerProcessing/ -> AutoQMYZ/ -> 项目根目录)
current_dir = dirname(current_dir)
current_dir = dirname(current_dir)

# 通过本地获取答案
def get_answer_by_local(question, course_name):
    # 本地题库位置
    question_data_dir = current_dir + '\\Data\\Question_data'
    question_data_main = question_data_dir + '\\' + course_name + '.csv'

    answer = []

    # 检查是否存在本地题库
    if not exists(question_data_main):
        print('本地题库不存在')
        return answer
    
    # 读取本地题库
    df = pd.read_csv(question_data_main).astype(str)

    # 查找题库
    row = df[df['question'] == question[1]]

    if len(row) > 0:
        answer = row.iloc[0]['right_answer']
        answer = answer[1:-1]
        answer = answer.split(", ")
        for i in range(len(answer)):
            answer[i] = answer[i][1:-1]
    else:
        print('本地题库没有找到该题')

    return answer

# 人工答题
def get_answer_by_human(question):
    print(question[0])
    print(question[1])
    for index, option in enumerate(question[2], start=1):
        print(f"{index} : {option}")

    answer = input('请在此处输入答案(序号,多个请用空格隔开):')
    input_error = True
    while input_error:
        input_error = False
        if answer != '':
            answer_list = answer.split(" ")
            answer = []
            if question[0] == '单选题' and len(answer_list) > 1:
                input_error = True
            else:
                for ans in answer_list:
                    try:
                        ans = int(ans)
                        if ans < 0 or ans > len(question[2]):
                            input_error = True
                            break
                    except:
                        input_error = True
                        break
        else:
            input_error = True

        if input_error:
            answer = input('你的输入非法, 请在此处输入答案(序号,多个请用空格隔开):')

    for ans in answer_list:
        ans = int(ans)
        answer.append(question[2][ans-1])

    return answer

def get_page_countdown(driver):
    if driver is None:
        return None
    try:
        from selenium.webdriver.common.by import By
        element = driver.find_element(By.XPATH, "/html/body/div/div/div/div")
        text = element.text.strip()
        match = re.search(r'\d+', text)
        if match:
            return int(match.group())
    except Exception:
        pass
    return None

# 人工答题（带超时）
def get_answer_by_human_timeout(question, timeout, driver=None):
    print(f"\n=================== 人工作答 (限时 {timeout} 秒) ===================")
    print(f"【题型】: {question[0]}")
    print(f"【题目】: {question[1]}")
    for index, option in enumerate(question[2], start=1):
        print(f"  {index} : {option}")
    print("----------------------------------------------------------------")
    
    import threading
    thread_name = threading.current_thread().name
    if thread_name.startswith("task_"):
        task_id = thread_name[5:]
        
        # 获取网页倒计时并动态计算实际超时
        countdown = get_page_countdown(driver)
        actual_timeout = timeout
        if countdown is not None:
            actual_timeout = min(countdown - 1, timeout)
            print(f"[Manual] Page countdown is {countdown}s. Actual timeout set to {actual_timeout}s.")
            
        # 将问题存入全局状态
        manual_questions[task_id] = {
            "question": question,
            "timeout": actual_timeout,
            "start_time": time.time(),
            "answer": None
        }
        
        print(f"[Manual] Waiting for WebUI input for task: {task_id}...")
        start_time = time.time()
        while time.time() - start_time < actual_timeout:
            # 1. 检查 WebUI 的答案
            q_info = manual_questions.get(task_id)
            if q_info and q_info["answer"] is not None:
                answer = q_info["answer"]
                manual_questions.pop(task_id, None)
                print(f"[Manual] Received WebUI answer: {answer}")
                return answer
                
            # 2. 检查网页倒计时是否即将结束 (<=1秒 触发避险)
            current_countdown = get_page_countdown(driver)
            if current_countdown is not None and current_countdown <= 1:
                print(f"[Manual] Page countdown reached {current_countdown}s (<=1s). Triggering emergency random selection.")
                manual_questions.pop(task_id, None)
                if len(question) > 2 and question[2]:
                    r_ans = [random.choice(question[2])]
                    print(f"【紧急避险】倒计时剩余 {current_countdown} 秒，强制随机答题: {r_ans}")
                    return r_ans
                return []
                
            time.sleep(0.2)
            
        manual_questions.pop(task_id, None)
        print("[Manual] Timeout or countdown expired. Failsafe random selection...")
        if len(question) > 2 and question[2]:
            return [random.choice(question[2])]
        return []
    else:
        # 控制台输入回退
        countdown = get_page_countdown(driver)
        actual_timeout = timeout
        if countdown is not None:
            actual_timeout = min(countdown - 1, timeout)
            
        prompt = f"请在此处输入答案序号 (多个请用空格隔开，超时将跳过): "
        sys.stdout.write(prompt)
        sys.stdout.flush()
        
        start_time = time.time()
        input_str = ''
        
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getwche()
                if char in ('\r', '\n'):
                    sys.stdout.write('\n')
                    break
                elif char == '\b':  # Backspace
                    if len(input_str) > 0:
                        input_str = input_str[:-1]
                        sys.stdout.write(' \b')
                        sys.stdout.flush()
                else:
                    input_str += char
                    
            if time.time() - start_time > actual_timeout:
                sys.stdout.write('\n[超时已过，跳过当前人工作答]\n')
                if len(question) > 2 and question[2]:
                    return [random.choice(question[2])]
                return []
                
            # 命令行下实时倒计时避险检查
            current_countdown = get_page_countdown(driver)
            if current_countdown is not None and current_countdown <= 1:
                sys.stdout.write('\n[网页倒计时即将结束 (<=1秒)，强制随机答题]\n')
                if len(question) > 2 and question[2]:
                    return [random.choice(question[2])]
                return []
                
            time.sleep(0.05)
            
        cleaned_input = input_str.strip()
        if not cleaned_input:
            if len(question) > 2 and question[2]:
                return [random.choice(question[2])]
            return []
            
        answer_list = cleaned_input.split()
        answer = []
        
        for ans in answer_list:
            try:
                ans_idx = int(ans)
                if 1 <= ans_idx <= len(question[2]):
                    answer.append(question[2][ans_idx - 1])
            except ValueError:
                pass
                
        if not answer and len(question) > 2 and question[2]:
            return [random.choice(question[2])]
        return answer

# 通过 OpenAI 兼容 API 获取答案（单次调用）
def get_answer_by_ai_mini(question, ai_config):
    """
    使用 OpenAI 兼容的 Chat Completions API 获取答案。

    参数：
    question: 一个三元组 (题型, 题目, 选项列表)
    ai_config: 包含 'api_key', 'base_url', 'model' 的字典

    返回：
    包含选中选项文字的列表。
    """
    # 构造提示词
    prompt = (
        f"我想问你一个{question[0]}，题目是{question[1]}，有这些选项："
        + ", ".join(f"{chr(65+i)}.{opt}" for i, opt in enumerate(question[2]))
        + "。请直接返回字母（多选请用空格分隔）："
    )

    # API 请求地址
    url = f"{ai_config['base_url'].rstrip('/')}/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ai_config['api_key']}"
    }

    payload = {
        "model": ai_config['model'],
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "max_tokens": 800,
        "top_p": 0.4,
    }

    # 重试机制
    for attempt in range(3):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            break
        except requests.RequestException as e:
            if attempt < 2:
                time.sleep(3)
            else:
                print(f"请求失败: {e}")
                return []

    data = response.json()
    # 提取模型返回文本
    content_part = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

    # 使用正则匹配所有大写字母作为答案
    letters = re.findall(r"[A-Z]", content_part)
    answers = []
    for letter in letters:
        idx = ord(letter) - 65
        if 0 <= idx < len(question[2]):
            answers.append(question[2][idx])
    return answers

# 通过 AI 获取答案（多次验证）
def get_answer_by_ai(question, ai_config):
    answer_list_tmp = []
    answer = []

    for i in range(3):
        if i == 0:
            print(f"正在获取AI回答...({i})")
            answer_list_tmp.append(get_answer_by_ai_mini(question, ai_config))
        else:
            print(f"正在获取AI回答...({i})")
            answer_tmp = get_answer_by_ai_mini(question, ai_config)
            if answer_tmp in answer_list_tmp:
                answer = answer_tmp
                break
    
    # print(answer_list_tmp)

    return answer

# 通过所有方式获取答案
def get_answer_by_all(question, course_name, driver=None):
    # 加载答题优先级配置
    ans_config = load_answer_config()
    priority = ans_config.get("answer_priority", ["db", "ai", "manual", "random"])
    manual_timeout = ans_config.get("manual_timeout", 30.0)
    
    # 紧急避险检查：如果页面倒计时已经 <= 1秒，直接强制随机，免去其他策略带来的额外延迟
    countdown = get_page_countdown(driver)
    if countdown is not None and countdown <= 1:
        if len(question) > 2 and question[2]:
            answer = [random.choice(question[2])]
            print(f"【进入答题前紧急避险】倒计时已不足 {countdown} 秒 (<=1秒)，强制随机答题: {answer}")
            return answer
            
    answer = []
    
    for strategy in priority:
        # 重复的避险检测 (在轮询各策略时)
        current_countdown = get_page_countdown(driver)
        if current_countdown is not None and current_countdown <= 1:
            if len(question) > 2 and question[2]:
                answer = [random.choice(question[2])]
                print(f"【中途紧急避险】倒计时已不足 {current_countdown} 秒 (<=1秒)，强制随机答题: {answer}")
                break
                
        if strategy == "db":
            answer = get_answer_by_local(question, course_name)
            if answer:
                print(f"【题库】回答: {answer}")
                break
        elif strategy == "ai":
            ai_config = load_ai_config()
            if ai_config is not None:
                answer = get_answer_by_ai(question, ai_config)
                if answer:
                    print(f"【AI】回答: {answer}")
                    break
        elif strategy == "manual":
            answer = get_answer_by_human_timeout(question, manual_timeout, driver)
            if answer:
                print(f"【人工】回答: {answer}")
                break
        elif strategy == "random":
            if len(question) > 2 and question[2]:
                answer = [random.choice(question[2])]
                print(f"【随机】回答: {answer}")
                break
                
    if not answer:
        if len(question) > 2 and question[2]:
            answer = [random.choice(question[2])]
            print(f"【保底随机】回答: {answer}")
            
    return answer

def get_answer_by_all_right(question, course_name):
    answer = get_answer_by_local(question, course_name)

    return answer

if __name__ == '__main__':
    get_answer_by_all(['单选题', '共产党员有权在党的会议上有根据地批评党的任何组织和任何党员,向党负责地揭发、检举()的事实,要求处分违法乱纪的党员,要求罢免或撤换不称职的干部.', ['党的任何组织和任何党员违法乱纪', '党的任何组织违法乱纪', '党的任何党员违法乱纪']], 
                      '中国近现代史纲要')
