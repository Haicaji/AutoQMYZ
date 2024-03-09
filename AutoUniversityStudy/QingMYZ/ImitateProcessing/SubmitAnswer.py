import re

from selenium.webdriver.common.by import By
from time import sleep

from AutoUniversityStudy.QingMYZ.ImitateProcessing.StandardQuestion import standard_question

# 判断是否有频率限制
def ban_quickly(driver):
    mui_bottun = driver.find_element(By.CSS_SELECTOR, 
                                     'body > div.mui-popup.mui-popup-in > div.mui-popup-buttons > span.mui-popup-button.mui-popup-button-bold')
    mui_bottun.click()
    print("答题过快, 暂停30秒...")
    sleep(30)

# 判断是否有休息提醒
def ban_rest(driver):
    mui_bottun = driver.find_element(By.CSS_SELECTOR, 
                                     'body > div.mui-popup.mui-popup-in > div.mui-popup-buttons > span.mui-popup-button.mui-popup-button-bold')
    mui_bottun.click()

def exist_mui(driver):
    try_times = 0
    while True: 
        try:
            mui_title = driver.find_element(By.CSS_SELECTOR, 
                                            'body > div.mui-popup.mui-popup-in > div.mui-popup-inner > div.mui-popup-title')
            break
        except Exception as e:
            try_times += 1
            if try_times > 1:
                return driver
    if mui_title.text == '系统提示' or mui_title.text == '系统提醒':
        driver = ban_rest(driver)
    elif mui_title.text == '提示' or mui_title.text == '提醒':
        driver = ban_quickly(driver)
    else:
        print("出现其他弹窗")

    return driver

# 判断是否超时
def over_time(driver):
    question_header= driver.find_element(By.CSS_SELECTOR, 
                                        '#wrapper > div > div')
    time = question_header.text.split('\n')[1]
    
    if int(time) <= 3:
        sleep(int(time)+0.3)
        return True
    else:
        return False

# 点击答案
def click_answer(driver, answer, question_type, question):
    right_answer = ''
    answer_sucess = False

    # 判断是否超时
    if_right = over_time(driver)
    if if_right == False:
        # 判断是否为多选
        # 多选题目
        if question_type == '多选题':
            while True:
                options_ = driver.find_elements(By.CSS_SELECTOR,
                                                "#wrapper > div.content > dl > dd")
                sure = driver.find_element(By.CSS_SELECTOR, 
                                           "#wrapper > div > button")
                try:
                    for option in options_:
                        if standard_question(option.text) in answer:
                            if option.get_attribute('style') == '':
                                option.click()
                    # 点击确定
                    sure.click()
                    # 判断答案是否正确
                    if_right = driver.find_element(By.CSS_SELECTOR, 
                                                   "#mask > div.frame > h1")
                    break
                except:
                    exist_mui(driver)
        # 单选题目
        else:
            options_ = driver.find_elements(By.CSS_SELECTOR, 
                                '#wrapper > div.content > dl > dd')
            for option in options_:
                if standard_question(option.text) in answer:
                    try_time = 0
                    while True:
                        try:
                            option.click()
                            # 判断答案是否正确
                            if_right = driver.find_element(By.CSS_SELECTOR, "#mask > div.frame > h1")
                            break
                        except Exception as e:
                            try_time+=1
                            if try_time > 1:
                                raise e
                            exist_mui(driver)
                    break
    else:
        if_right = driver.find_element(By.CSS_SELECTOR, "#mask > div.frame > h1")
    
    # 获取正确答案
    if '加油' in if_right.text:
        right_answer_ =  driver.find_element(By.CSS_SELECTOR, 
                                   "#mask > div.frame > p")
        right_answer = right_answer_.text
        right_answer = right_answer.replace('答案', '')[1:]+'、A'
        right_answer = re.findall(r"[A-Z]\..+?(?=、[A-Z])", right_answer)
        for i in range(len(right_answer)):
            right_answer[i] = standard_question(right_answer[i])
    else:
        right_answer = answer
        answer_sucess = True

    # 点击下一题
    next = driver.find_element(By.CSS_SELECTOR, 
                                "#mask > div.frame > div > span:nth-child(1)")
    try_time = 1
    while True:
        try:
            next.click()
            break
        except Exception as e:
            try_time += 1
            if try_time > 1:
                print('点击下一题失败')
                raise e
            exist_mui(driver)

    return right_answer, answer_sucess