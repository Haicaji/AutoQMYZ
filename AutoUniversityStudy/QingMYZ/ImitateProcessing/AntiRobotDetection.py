# 判断是否为刷题检测题
def detect_error(question):
    if '刷题' in question[0]:
        print('\n\n出现防刷题题目\n\n')
        return True