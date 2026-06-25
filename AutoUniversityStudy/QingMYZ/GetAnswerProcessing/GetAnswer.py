# 获取答案
import json
import pandas as pd
import requests
import time
import re

from os.path import exists, abspath, dirname
from time import sleep

# 当前所在绝对路径
current_dir = dirname(abspath(__file__))
# 返回上一级目录
current_dir = dirname(current_dir)
current_dir = dirname(current_dir)
current_dir = dirname(current_dir)

# 通过本地获取答案
def get_answer_by_local(question, course_name):
    # 本地题库位置
    question_data_dir = current_dir + '\\Data\\Question_data\\QingMYZ'
    question_data_main = 'question_main.csv'
    question_data_dir += '\\' + course_name 
    question_data_main = question_data_dir + '\\' + question_data_main

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

# 通过gemini获取答案
def get_answer_by_gemini_mini(question, api_key):
    """
    使用 Google Gemini 2.0 Flash API 获取多选题答案。

    参数：
    question: 一个三元组 (题型, 题目, 选项列表)
    api_key: Google API 密钥

    返回：
    包含选中选项文字的列表。
    """
    # 构造提示词
    prompt = (
        f"我想问你一个{question[0]}，题目是{question[1]}，有这些选项："
        + ", ".join(f"{chr(65+i)}.{opt}" for i, opt in enumerate(question[2]))
        + "。请直接返回字母（多选请用空格分隔）："
    )

    # 安全设置
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT",  "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH",  "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    # 生成配置
    generation_config = {
        "temperature": 0,
        "maxOutputTokens": 800,
        "topP": 0.4,
        "topK": 10,
        # 可选：指定 MIME 类型为 JSON
        "responseMimeType": "application/json"
    }

    # API 请求地址，使用 Gemini 2.0 Flash 模型
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}"
    )

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "safetySettings": safety_settings,
        "generationConfig": generation_config
    }

    # 重试机制
    for attempt in range(3):
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json; charset=utf-8"},
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
    content_part = data.get("candidates", [])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

    # 使用正则匹配所有大写字母作为答案
    letters = re.findall(r"[A-Z]", content_part)
    answers = []
    for letter in letters:
        idx = ord(letter) - 65
        if 0 <= idx < len(question[2]):
            answers.append(question[2][idx])
    return answers

def get_answer_by_gemini(question, API_KEY):
    answer_list_tmp = []
    answer = []

    for i in range(3):
        if i == 0:
            print(f"正在获取gemini回答...({i})")
            answer_list_tmp.append(get_answer_by_gemini_mini(question, API_KEY))
        else:
            print(f"正在获取gemini回答...({i})")
            answer_tmp = get_answer_by_gemini_mini(question, API_KEY)
            if answer_tmp in answer_list_tmp:
                answer = answer_tmp
                break
    
    # print(answer_list_tmp)

    return answer

# 通过所有方式获取答案
def get_answer_by_all(question, API_KEY, course_name):
    answer = get_answer_by_local(question, course_name)
    if answer == []:
        if 'Gemini' in API_KEY.keys(): 
            answer = get_answer_by_gemini(question, API_KEY['Gemini'])
        else:
            API_KEY_File = current_dir + '\\Data\\API_key\\Gemini\\key.txt'
            with open(API_KEY_File, 'r', encoding='utf-8') as f:
                API_KEY = f.read()
            if API_KEY != '':
                answer = get_answer_by_gemini(question, API_KEY)

        # answer = get_answer_by_gemini_mini(question)
        if answer == []:
            # answer = get_answer_by_human(question)
            answer = question[-1][0]
            print("随机答案：" + answer)
        else:
            print(f"gemini回答{answer}")
    else:
        print(f"本地题库回答{answer}")

    return answer

def get_answer_by_all_right(question, course_name):
    answer = get_answer_by_local(question, course_name)

    return answer

if __name__ == '__main__':
    get_answer_by_all(['单选题', '共产党员有权在党的会议上有根据地批评党的任何组织和任何党员,向党负责地揭发、检举()的事实,要求处分违法乱纪的党员,要求罢免或撤换不称职的干部.', ['党的任何组织和任何党员违法乱纪', '党的任何组织违法乱纪', '党的任何党员违法乱纪']], 
                      {},
                      '中国近现代史纲要')