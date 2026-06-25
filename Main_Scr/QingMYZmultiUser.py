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
        # 判断是否进入finish文件夹
        if 'finish' in root:
            continue
        else:
            finish_dir = root.replace(user_data_dir, user_data_dir + '\\finish')
            # 判断是否存在文件夹
            if not os.path.exists(finish_dir):
                os.makedirs(finish_dir)
            for file in files:
                if file.endswith('.json'):
                    print(file)
                    with open(os.path.join(root, 'log.txt'), 'a', encoding='utf-8') as f:
                        f.write('-----------------------------\n')
                        f.write('开始进行'+os.path.join(root, file)+'\n')
                    Q = QingMYZClass(os.path.join(root, file))
                    Q.mainProcess()
                    # 已经完成
                    if Q.del__():
                        os.rename(os.path.join(root, file), os.path.join(finish_dir, file))
                    with open(os.path.join(root, 'log.txt'), 'a', encoding='utf-8') as f:
                        f.write('结束'+os.path.join(root, file)+'\n')
                        f.write('-----------------------------\n')

if __name__ == '__main__':
    multi_user_main()