import pandas as pd
from os.path import exists

question_data_dir = './question_data/'
question_data_main = './question_data/question_main.csv'

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
def after_answer(question, right_answer):
    # 判断是否存在csv文件
    if not exists(question_data_main):
        creat_csv(question_data_main)

    # 添加数据
    add_question_to_csv(question_data_main, question, right_answer)

if __name__ == '__main__':
    a = after_answer(['单选题', 
                  '11921年7月,中共第一次全国代表召开于()', 
                  ['A.北京', 'B.上海', 'C.广州', 'D.武汉']], ['A.北京'])
    