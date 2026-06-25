import pandas as pd
import os

# 题库位置
question_data_dir = ''
question_data_main = ''

# 去重率统计
quesion_num = 0
re_question_num = 0
end_question_num = 0

# 合并两个csv文件, 并去重
def combine_question_csv(csv_file):
    # 初始化题数
    main_num = 0
    sec_num = 0
    end_num = 0

    # 读取两个csv文件
    df_main = pd.read_csv(question_data_main).astype(str)
    df_sec = pd.read_csv(csv_file).astype(str)

    # 获取题数
    main_num = len(df_main)
    sec_num = len(df_sec)

    # 合并两个DataFrame
    df_merged = pd.concat([df_main, df_sec])

    # 根据question和right_answer列去重, 保留第一个出现的行
    df_merged = df_merged.drop_duplicates(subset=['question', 'right_answer'])
    # 临时保存合并后的DataFrame
    df_merged.to_csv(question_data_dir + 'merged_tmp.csv', index=False)

    # 根据question列找出重复的行
    df_merged_ = df_merged[df_merged.duplicated(subset=['question'], keep=False)]
    # 保存只有question列的重复行
    df_merged_.to_csv(question_data_dir + 'different_answer.csv', index=False)

    # 重新打开csv文件
    df_merged = pd.read_csv(question_data_dir + 'merged_tmp.csv').astype(str)
    df_merged_ = pd.read_csv(question_data_dir + 'different_answer.csv').astype(str)

    df_merged_n = df_merged[~df_merged.isin(df_merged_)].dropna()

    df_merged_n.to_csv(question_data_dir + 'question_main.csv', index=False)

    # 获取合并后题数
    end_num = len(df_merged_n)

    # 删除临时文件
    os.remove(question_data_dir + 'merged_tmp.csv')
    if len(df_merged_) > 0:
        print(f'合并文件存在答案歧义,详细请看{question_data_dir}different_answer.csv')
    else:
        os.remove(question_data_dir + 'different_answer.csv')

    print(f'合并文件{csv_file}完成')
    print(f'主题库题数: {main_num}, 二级题库题数: {sec_num}')
    print(f'合并后题数: {end_num}, 重复题数(含答案歧义): {(main_num + sec_num - end_num)}')

# 获取所有要合并的文件
def get_question_csv():
    # 遍历所有csv文件
    csv_files = []
    for root, dirs, files in os.walk(question_data_dir):
        for file in files:
            if file.endswith('.csv'):
                if os.path.join(root, file) == question_data_main:
                    continue
                csv_files.append(os.path.join(root, file))

    for csv_file in csv_files:
        combine_question_csv(csv_file)

if __name__ == '__main__':
    question_data_dir = input('请输入题库目录:').replace("\"", "")
    question_data_main = input('请输入主题库文件路径:').replace("\"", "")
    get_question_csv()