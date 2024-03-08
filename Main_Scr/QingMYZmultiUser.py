import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from AutoUniversityStudy.QingMYZ.QingMYZMain import QingMYZClass

# 当前所在绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 返回上一级目录
current_dir = os.path.dirname(current_dir)
# 用户数据位置
user_data_dir = current_dir + '\\Data\\User\\QingMYZ'

def multi_user_main():
    # 遍历目录下的所有json文件
    for root, dirs, files in os.walk(user_data_dir):
        for file in files:
            if file.endswith('.json'):
                Q = QingMYZClass(os.path.join(root, file))
                Q.mainProcess()
                Q.del__()

if __name__ == '__main__':
    multi_user_main()