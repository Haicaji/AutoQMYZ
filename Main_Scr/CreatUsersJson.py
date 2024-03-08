import json
import os

# 当前所在绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 返回上一级目录
current_dir = os.path.dirname(current_dir)
# 用户数据位置
user_data_dir = current_dir + '\\Data\\User\\QingMYZ'

# 修改用户数据文件
def change_user_json(user_data_file_name):
    # 读取用户数据文件
    with open(f'{user_data_dir}\\{user_data_file_name}.json', 'r', encoding='utf-8') as f:
        user_data = json.load(f)
    
    with open(f'{user_data_dir}\\{user_data_file_name}.json', 'w', encoding='utf-8') as f:
        for key in user_data.keys():
            for sub_key in user_data[key].keys():
                tmp = input(f'请输入{key}的{sub_key}数据(原本为{user_data[key][sub_key]},回车不更改):')
                if tmp != '':
                    user_data[key][sub_key] = tmp
        json.dump(user_data, f, separators=(',', ':'), ensure_ascii=False)

# 创建用户数据文件
def creat_user_json():
    user_data_file_name = input('请输入用户数据文件名:')
    user_data = {
        'user': {
            'account': '', 
            'password': '', 
            'verify_request': ''
            }, 
        'API_key': {
            'Gemini': '', 
            'ChatGPT': '', 
            'NewBing': ''},
        'answer_setting':{
            'aim_questions_num_total': '', 
            'questions_num_day_max': '', 
            'course_name': '', 
            'low_right_rate': '', 
            'top_right_rate': '',
            'min_question_time': ''
            },
        'now': {'questions_num_now': ''},
        'other': {}
    }

    # 判断数据文件是否已经存在
    if os.path.exists(f'{user_data_dir}\\{user_data_file_name}.json'):
        print('用户数据文件已经存在, 是否进行修改(Y/n)')
        if input() == '' or input() == 'Y' or input() == 'y':
            change_user_json(user_data_file_name)
    else:
        # 输入数据
        for key in user_data.keys():
            for sub_key in user_data[key].keys():
                user_data[key][sub_key] = input(f'请输入{key}的{sub_key}数据:')

        with open(f'{user_data_dir}\\{user_data_file_name}.json', 'w', encoding='utf-8') as f:
            json.dump(user_data, f, separators=(',', ':'), ensure_ascii=False)

if __name__ == '__main__':
    creat_user_json()