# 获取答案
import pandas as pd
from os.path import exists, abspath, dirname
import requests
import json
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
        answer.append(question[2][ans-1])

    return answer

# 通过gemini获取答案
def get_answer_by_gemini_mini(question, API_KEY):
    # 设置提问词
    text = "我想问你一个" + question[0] + ", 题目是" + question[1] + ", 有这些选项"
    i = 0
    for option in question[2]:
        text += chr(65 + i) + '.' + option + ", "
        i += 1
    text += "请你直接给我回答字母(如果是多选回复多个字母, 用空格隔开):"

    # 提示词参数
    safetySettings = [{
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE"
        }]
    generationConfig = {
        "stopSequences": [
            "Title"
        ],
        "temperature": 0,
        "maxOutputTokens": 800,
        "topP": 0.4,
        "topK": 10
    }

    # api地址
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:streamGenerateContent?key={API_KEY}"

    # 请求头
    headers = {
        'Content-Type': 'application/json',
    }

    # 请求数据
    data = {
        'safetySettings': safetySettings,
        'generationConfig': generationConfig,
        "contents": [
            {
                'role': 'user',
                "parts": [
                    {
                        "text": text
                     }
                ]
            }
        ]
    }
    try_times = 0
    while True:
        try:
            # 请求
            response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)

            # 打印请求结果
            # print(response.json())

            # 判断请求是否成功
            if response.status_code != 200:
                raise ValueError("Failed to generate response: " + response.text)

            break
        except Exception as e:
            try_times += 1
            if try_times > 3:
                return []
            print(f"网络不稳定, 正在重试... {try_times}")
            sleep(3)

    # 接受答案
    for line in response.iter_lines():
        if b"text" in line:
            answer = json.loads(line.decode('utf-8').split(':')[1])
            break
    
    # 处理返回的答案
    answer_list = answer.split(" ")
    answer = []
    for ans in answer_list:
        try:
            if ord(ans) >= 65 and ord(ans) < 65 + len(question[2]):
                answer.append(question[2][ord(ans) - 65])
        except:
            break
        
    return answer

def get_answer_by_gemini(question, API_KEY):
    answer_list_tmp = []
    answer = []

    for i in range(3):
        if i == 0:
            answer_list_tmp.append(get_answer_by_gemini_mini(question, API_KEY))
        else:
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
        if 'Gemini' in API_KEY.keys(): answer = get_answer_by_gemini(question, API_KEY['Gemini'])
        # answer = get_answer_by_gemini_mini(question)
        if answer == []:
            answer = get_answer_by_human(question)
            # answer = question[-1][0]
        else:
            print(f"gemini回答{answer}")
    else:
        print(f"本地题库回答{answer}")

    return answer

if __name__ == '__main__':
    get_answer_by_all(['单选题', '共产党员有权在党的会议上有根据地批评党的任何组织和任何党员,向党负责地揭发、检举()的事实,要求处分违法乱纪的党员,要求罢免或撤换不称职的干部.', ['党的任何组织和任何党员违法乱纪', '党的任何组织违法乱纪', '党的任何党员违法乱纪']], {})