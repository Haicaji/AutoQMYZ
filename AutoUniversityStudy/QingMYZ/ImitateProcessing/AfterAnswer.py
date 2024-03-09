import pandas as pd

from os.path import exists, abspath, dirname
from os import makedirs

# 当前所在绝对路径
current_dir = dirname(abspath(__file__))
# 返回上一级目录
current_dir = dirname(current_dir)
current_dir = dirname(current_dir)
current_dir = dirname(current_dir)

# 初始化一个csv文件
def creat_csv(csv_file):
    # 列名
    columns = ['question', 'options', 'right_answer']

    # 创建一个空的 DataFrame
    df = pd.DataFrame(columns = columns)

    # 将 DataFrame 保存到 CSV 文件中
    df.to_csv(csv_file, index=False)

# 写入数据
def add_question_to_csv(csv_file, question, right_answer):
    # 从 CSV 文件中读取数据到 DataFrame
    df = pd.read_csv(csv_file)
    
    # 判断题库中是否已经存在该题目
    if question[1] in df['question'].values:
        print(f'"{question[1]}"该题目已存在')
        return

    new_row = {'question': question[1], 
               'options': question[2], 
               'right_answer': right_answer}

    # 将新行添加到 DataFrame 中
    df = df._append(new_row, ignore_index=True)

    # 将更新后的 DataFrame 保存回 CSV 文件中
    df.to_csv(csv_file, index=False)

# 答题后操作
def after_answer(question, right_answer, course_name):
    # 本地题库位置
    question_data_dir = current_dir + '\\Data\\Question_data\\QingMYZ'
    question_data_main = 'question_main.csv'
    question_data_dir += '\\' + course_name 
    question_data_main = question_data_dir + '\\' + question_data_main

    # 判断是否存在csv文件
    if not exists(question_data_main):
        # 判断是否存在文件夹
        if not exists(question_data_dir):
            makedirs(question_data_dir)
        creat_csv(question_data_main)

    # 添加数据
    add_question_to_csv(question_data_main, question, right_answer)
    