from fake_useragent import UserAgent

# 判断是否为刷题检测题
def detect_error(question):
    if '刷题' in question[0]:
        print('\n\n出现防刷题题目\n\n')
        return True
    
# 随机生成UA
def get_ua():
    user_agent = UserAgent()
    ua =  user_agent.random

    return ua

if __name__ == '__main__':
    print(get_ua())