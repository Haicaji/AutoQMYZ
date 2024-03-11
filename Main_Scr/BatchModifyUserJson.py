# 批量修改用户json
import json
import os

def change_dict(dict_main, dict_tem):
    for key in dict_tem.keys():
        if key == 'b3' or key == 'b4':
            pass
        if key in dict_main.keys():
            # 判断一个dict_tem[key]是不是字典
            if isinstance(dict_tem[key], dict):
                change_dict(dict_main[key], dict_tem[key])
            else: 
                dict_main[key] = dict_tem[key]
        else:
            if not isinstance(dict_tem[key], dict):
                dict_main[key] = dict_tem[key]

def change_user_json(user_data_file_name, template_data):
    # 读取用户数据文件
    with open(user_data_file_name, 'r', encoding='utf-8') as f:
        user_data = json.load(f)
    
    with open(user_data_file_name, 'w', encoding='utf-8') as f:
        change_dict(user_data, template_data)

        json.dump(user_data, f, separators=(',', ':'), ensure_ascii=False)

if __name__ == '__main__':
    user_data_dir = input('请输入要批量修改的用户数据文件夹:').replace('\"', '')
    template_json = input('请输入要批量修改的模板json文件路径:').replace('\"', '')

    with open(template_json, 'r', encoding='utf-8') as f:
        template_data = json.load(f)

    # 遍历所有json文件
    for root, dirs, files in os.walk(user_data_dir):
        for file in files:
            if file.endswith('.json'):
                change_user_json(os.path.join(root, file), template_data)
