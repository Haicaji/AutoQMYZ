import re

# 题目标准化
def standard_question(text):
    text = re.sub('\s', '', text)
    text = re.sub('[A-Z]\.', '', text)
    text = text.replace('（', '(')
    text = text.replace('）', ')')
    text = text.replace('，', ',')
    text = text.replace('。', '.')

    return text