# 题目标准化
def standard_question(text):
    text = text.replace(' ', '')
    text = text.replace('（', '(')
    text = text.replace('）', ')')
    text = text.replace('，', ',')
    text = text.replace('。', '.')

    return text