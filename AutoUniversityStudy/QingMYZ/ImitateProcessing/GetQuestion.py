from QingMa.StandardQuestion import standard_question

from selenium.webdriver.common.by import By

# 获取题目
def get_question(driver):
    '''
    question = ['题目类型', 
                '题目', 
               ['选项1', '选项2', '选项3', '选项4']]
    '''
    question = []

    question_type = driver.find_element(By.CSS_SELECTOR, 
                                        '#wrapper > div > div')
    question.append(question_type.text.split('\n')[0])

    question_des = driver.find_element(By.CSS_SELECTOR, 
                                       '#wrapper > div > dl > dt')
    question.append(standard_question(question_des.text))

    try_times = 0
    while True:
        options = []
        try:
            options_ = driver.find_elements(By.CSS_SELECTOR, 
                                            '#wrapper > div.content > dl > dd')
            for option in options_:
                options.append(standard_question(option.text))
        except Exception as e:
            try_times += 1
            if try_times == 2:
                raise e
            else:
                continue
        question.append(options)
        break

    return question