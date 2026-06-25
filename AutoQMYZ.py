import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from AutoQMYZ.QingMYZMain import QingMYZClass
from AutoQMYZ.Logger import setup_logging

# 当前所在绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 返回上一级目录
current_dir = os.path.dirname(current_dir)
# 用户数据位置
user_data_dir = current_dir + '\\Data\\User'

def multi_user_main():
    # 初始化全局日志系统
    setup_logging()
    
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
                    print(f"=====================================")
                    print(f"开始处理配置文件: {os.path.join(root, file)}")
                    
                    Q = QingMYZClass(os.path.join(root, file))
                    Q.mainProcess()
                    # 已经完成
                    if Q.del__():
                        os.rename(os.path.join(root, file), os.path.join(finish_dir, file))
                    
                    print(f"结束处理配置文件: {os.path.join(root, file)}")
                    print(f"=====================================\n")

if __name__ == '__main__':
    multi_user_main()